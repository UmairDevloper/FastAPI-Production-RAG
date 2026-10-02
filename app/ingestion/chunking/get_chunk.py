"""
Chunker: parsed sections -> embedding-ready chunks (LangChain splitter)
=======================================================================

Reads ``parsed_sections.jsonl`` (output of the parser) and splits the
sections into chunks of a controlled size, ready for embeddings and a vector
database.

Why no heading splitter?
------------------------
The parser already split every page by heading and recorded the heading path,
so we only need to control the SIZE here.

Steps
-----
1. **Merge tiny sections.** A section shorter than ``MIN_CHARS`` (for example
   a "Recap" with one line) is joined with the next section of the same page,
   because very small chunks retrieve poorly. The merged heading is kept in the
   text as a markdown heading.
2. **Split long sections** with LangChain's ``RecursiveCharacterTextSplitter``
   in markdown mode. It prefers headings, then code fences, then paragraphs,
   then lines, then sentences, so it cuts at natural boundaries.
3. **Attach metadata** to every chunk: url, section url, headings, category,
   code languages, and only the links/images that appear in that chunk.
4. **Add context.** ``contextual_text`` is the chunk with a breadcrumb
   (``Page > Heading > Subheading``) on top. Embed that field.
5. **Drop exact duplicates** (same text hash).

Sizes are measured in characters (about 4 characters per token in English).

Input   <project root>/data/fastapi_docs/parsed_sections.jsonl
Output  <project root>/data/fastapi_docs/chunks.jsonl

Each output line (one chunk):
    {
      "chunk_id": "a1b2c3d4e5f6-0003",
      "doc_id": "a1b2c3d4e5f6",
      "chunk_index": 3,                       # position inside the page
      "section_ids": ["a1b2c3d4e5f6-002"],    # source section(s)
      "url": "https://fastapi.tiangolo.com/tutorial/body/",
      "section_url": ".../tutorial/body/#create-your-data-model",
      "page_title": "Request Body",
      "category": "tutorial",
      "heading_path": ["Request Body", "Create your data model"],
      "text": "...",                         # store / show this
      "contextual_text": "Request Body > Create...\\n\\n...",   # embed this
      "has_code": true,
      "code_languages": ["python"],
      "char_count": 950,
      "links": [...],
      "images": [...],
      "content_hash": "9f86d081884c7d65"
    }

Setup (once)
------------
    uv add langchain-text-splitters

Run
---
    uv run python app/ingestion/chunking.py
"""

import hashlib
import json
import re
from itertools import groupby
from pathlib import Path
from typing import Iterator

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Same folder as the crawler and parser (this file lives in <project>/app/ingestion/)
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "fastapi_docs"
INPUT_PATH = DATA_DIR / "parsed_sections.jsonl"
OUTPUT_PATH = DATA_DIR / "chunks.jsonl"

MAX_CHARS = 1800      # maximum chunk size (about 450 tokens); larger keeps code samples whole
MIN_CHARS = 300       # sections smaller than this are merged with the next one
OVERLAP_CHARS = 150   # characters repeated between neighbouring chunks of one section

# Splitter in markdown mode: it tries to cut at headings, code fences,
# paragraphs, lines, sentences and words, in that order of preference.
# Created once and reused for every section.
SPLITTER = RecursiveCharacterTextSplitter.from_language(
    language=Language.MARKDOWN,
    chunk_size=MAX_CHARS,
    chunk_overlap=OVERLAP_CHARS,
)

# Opening code fence with a language label, e.g. "```python"
FENCE_LANG_RE = re.compile(r"^```([\w+#.-]+)\s*$", re.M)


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def sha(text: str, length: int = 16) -> str:
    """
    Return a short, stable SHA-256 hex digest of a string.

    Used to detect duplicate chunks.

    Args:
        text: Any string.
        length: Number of hex characters to keep.

    Returns:
        The first ``length`` characters of the SHA-256 hex digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def load_sections(path: Path) -> Iterator[dict]:
    """
    Read the parser's JSONL file one section at a time.

    Args:
        path: Path to ``parsed_sections.jsonl``.

    Yields:
        One section dict per line.

    Raises:
        FileNotFoundError: If the parser has not been run yet.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run the parser first.")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def unique_by(items: list[dict], key: str) -> list[dict]:
    """
    Remove duplicate dicts by one key, keeping the first occurrence.

    Args:
        items: List of dicts (for example links or images).
        key: The dict key that identifies a duplicate (``"url"`` or ``"src"``).

    Returns:
        The de-duplicated list in original order.
    """
    seen: set = set()
    result = []
    for item in items:
        if item[key] not in seen:
            seen.add(item[key])
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Step 1: merge tiny sections
# ---------------------------------------------------------------------------

def merge_small_sections(sections: list[dict]) -> list[dict]:
    """
    Merge consecutive small sections of ONE page into larger units.

    If the current unit is shorter than ``MIN_CHARS`` and the next section
    still fits within ``MAX_CHARS``, the next section is appended to it. Its
    heading is written into the text as a markdown heading so the structure
    is not lost. Metadata (links, images, section ids) is combined.

    Args:
        sections: All sections of one page, in page order.

    Returns:
        A list of units. Each unit has the same fields as a section, plus
        ``section_ids`` (every section that went into it).
    """
    units: list[dict] = []

    for sec in sections:
        if units:
            prev = units[-1]
            fits = len(prev["text"]) + len(sec["text"]) <= MAX_CHARS

            if len(prev["text"]) < MIN_CHARS and fits:
                heading = sec["heading_path"][-1] if sec["heading_path"] else ""
                level = max(sec.get("heading_level", 1), 1)
                addition = f"{'#' * level} {heading}\n\n{sec['text']}" if heading else sec["text"]

                prev["text"] += "\n\n" + addition
                prev["section_ids"].append(sec["section_id"])
                prev["links"] += sec.get("links", [])
                prev["images"] += sec.get("images", [])
                continue

        # Start a new unit (copy the lists so merging never edits the input)
        units.append(
            {
                **sec,
                "section_ids": [sec["section_id"]],
                "links": list(sec.get("links", [])),
                "images": list(sec.get("images", [])),
            }
        )
    return units


# ---------------------------------------------------------------------------
# Step 2 and 3: split a unit and build chunk records
# ---------------------------------------------------------------------------

def make_chunk_records(unit: dict, seen_hashes: set[str]) -> list[dict]:
    """
    Split one unit into chunks and attach all metadata.

    Links and images are attached only to the chunks whose text really
    contains them (the link text or the ``(Image: alt)`` marker). Chunks whose
    text was already produced elsewhere are skipped.

    Args:
        unit: One unit from :func:`merge_small_sections`.
        seen_hashes: Hashes of chunks already produced (updated in place).

    Returns:
        A list of chunk dicts (without ``chunk_id`` / ``chunk_index`` yet).
    """
    path = unit["heading_path"]

    # Breadcrumb for embeddings: "Page title > H2 > H3" (no repeated titles)
    breadcrumb = " > ".join(dict.fromkeys([unit["page_title"], *path]))

    all_links = unique_by(unit["links"], "url")
    all_images = unique_by(unit["images"], "src")

    records: list[dict] = []
    for piece in SPLITTER.split_text(unit["text"]):
        content_hash = sha(piece)
        if content_hash in seen_hashes:  # exact duplicate somewhere else in the docs
            continue
        seen_hashes.add(content_hash)

        languages = sorted(set(FENCE_LANG_RE.findall(piece)))

        records.append(
            {
                "doc_id": unit["doc_id"],
                "section_ids": unit["section_ids"],
                "url": unit["url"],
                "section_url": unit["section_url"],
                "page_title": unit["page_title"],
                "category": unit["category"],
                "heading_path": path,
                "text": piece,
                # Same text with its breadcrumb on top: embed THIS field
                "contextual_text": f"{breadcrumb}\n\n{piece}",
                "has_code": "```" in piece,
                "code_languages": languages,
                "char_count": len(piece),
                # Keep only the links / images that appear in this chunk
                "links": [l for l in all_links if l["text"] and l["text"] in piece],
                "images": [
                    i for i in all_images if i["alt"] and f"(Image: {i['alt']})" in piece
                ],
                "content_hash": content_hash,
            }
        )
    return records


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Chunk every page, write ``chunks.jsonl`` and print a quality report.

    Sections are read grouped by page (the parser writes them in page order).
    The report shows the size distribution, how many chunks contain code, and
    how many chunks have an unbalanced code fence (a code block that was cut
    in the middle). Use it to tune ``MAX_CHARS`` / ``MIN_CHARS`` before
    embedding.
    """
    seen_hashes: set[str] = set()
    sizes: list[int] = []
    pages = code_chunks = broken_code = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        # groupby works because all sections of one page are consecutive
        for doc_id, group in groupby(load_sections(INPUT_PATH), key=lambda r: r["doc_id"]):
            pages += 1

            doc_chunks: list[dict] = []
            for unit in merge_small_sections(list(group)):
                doc_chunks.extend(make_chunk_records(unit, seen_hashes))

            # Stable ids and the position of each chunk inside its page
            for index, chunk in enumerate(doc_chunks):
                chunk["chunk_index"] = index
                chunk["chunk_id"] = f"{doc_id}-{index:04d}"
                out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

                sizes.append(chunk["char_count"])
                code_chunks += chunk["has_code"]
                # An odd number of fence lines means a code block was cut
                broken_code += chunk["text"].count("```") % 2

    if not sizes:
        print("No chunks produced. Check that parsed_sections.jsonl is not empty.")
        return

    print(f"Pages:               {pages}")
    print(f"Chunks:              {len(sizes)}")
    print(f"Chunks with code:    {code_chunks}")
    print(f"Chunks cutting code: {broken_code}")
    print(f"Chars min/avg/max:   {min(sizes)} / {sum(sizes) // len(sizes)} / {max(sizes)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()