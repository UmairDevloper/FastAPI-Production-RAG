"""
FastAPI Docs Parser (markdown-it-py version)
============================================

Takes the raw crawled pages (``pages.jsonl`` from the crawler) and turns them
into clean, structured *sections* ready for chunking and embedding.

What changed compared to the regex version
------------------------------------------
Markdown is parsed by ``markdown-it-py`` (a CommonMark-compliant parser) into
a token tree. Headings, fenced code, lists, tables, links and images are read
from that tree, so there are no regex edge cases such as a ``# comment`` inside
code being mistaken for a heading, or a link with brackets in its label.
Regexes remain only for website noise (permalink anchors, version-tab labels).

What it does
------------
1. **Structure:** splits every page into sections by heading and records the
   heading path, e.g. ``["Request Body", "Create your data model"]``.
2. **Code:** fenced code blocks are kept exactly (only indentation and trailing
   spaces are tidied); the language is kept or guessed. Duplicate code blocks
   inside one section (Python-version variants) are kept once.
3. **Links:** ``[text](url)`` becomes ``text`` in the body. The URL goes to
   metadata (absolute URL, tagged internal / external / email).
4. **Images:** ``![alt](src)`` becomes ``(Image: alt)`` in the body. The image
   source goes to metadata.
5. **Lists, tables, quotes:** re-rendered as clean markdown, so their
   structure survives for the chunker.
6. **Noise:** permalink anchors (¶), attribute lists, raw HTML, boilerplate
   lines, Python-version labels and invisible unicode are removed.

Input   <project root>/data/fastapi_docs/pages.jsonl
Output  <project root>/data/fastapi_docs/parsed_sections.jsonl

Each output line (one section) looks like:
    {
      "doc_id": "a1b2c3d4e5f6",
      "section_id": "a1b2c3d4e5f6-003",
      "url": "https://fastapi.tiangolo.com/tutorial/body/",
      "section_url": ".../tutorial/body/#create-your-data-model",
      "page_title": "Request Body",
      "category": "tutorial",
      "heading_path": ["Request Body", "Create your data model"],
      "heading_level": 2,
      "text": "...markdown with ```python fenced code``` preserved...",
      "contextual_text": "Request Body > Create your data model\\n\\n...",
      "has_code": true,
      "code_languages": ["python"],
      "code_block_count": 2,
      "word_count": 120,
      "links": [{"text": "...", "url": "...", "type": "internal"}],
      "images": [{"alt": "...", "src": "..."}],
      "content_hash": "9f86d081884c7d65"
    }

Setup (once)
------------
    uv add markdown-it-py

Run
---
    uv run python app/ingestion/parse_docs.py
"""

import hashlib
import json
import re
import textwrap
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urljoin, urlparse

from markdown_it import MarkdownIt
from markdown_it.token import Token

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Same folder the crawler wrote to (this file lives in <project>/app/ingestion/)
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "fastapi_docs"
INPUT_PATH = DATA_DIR / "pages.jsonl"
OUTPUT_PATH = DATA_DIR / "parsed_sections.jsonl"

# Domain of the docs, used to tell internal links from external ones
DOCS_DOMAIN = "fastapi.tiangolo.com"

# Pages with fewer words than this (after cleaning) are dropped as empty
MIN_PAGE_WORDS = 20

# The markdown parser. "commonmark" is the strict standard; we also switch on
# tables and ~~strikethrough~~, which the docs use.
MD = MarkdownIt("commonmark").enable(["table", "strikethrough"])

# ---------------------------------------------------------------------------
# Regular expressions: only for website noise, not for markdown structure
# ---------------------------------------------------------------------------

# MkDocs attribute lists such as { #custom-id } or { .class-name }
ATTR_LIST_RE = re.compile(r"\{\s*[#.][^}\n]*\}")

# Raw HTML helpers (for <img> tags and tags the crawler left behind)
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
HTML_ATTR_ALT_RE = re.compile(r'alt\s*=\s*"([^"]*)"', re.I)
HTML_ATTR_SRC_RE = re.compile(r'src\s*=\s*"([^"]*)"', re.I)
HTML_ANY_TAG_RE = re.compile(r"</?[a-zA-Z][^>\n]*>")
HTML_BR_RE = re.compile(r"<br\s*/?>", re.I)

# Link labels that are only permalink anchors (the "¶" next to every heading)
PERMALINK_LABELS = {"", "¶", "#"}

# A whole paragraph that is boilerplate, or the "Python 3.10+" tab labels
# shown above code samples
BOILERPLATE_RE = re.compile(
    r"(?:skip to content|table of contents|back to top|edit this page|"
    r"was this page helpful\??|thanks for your feedback.*|"
    r"(?:Python\s*3\.\d+\+?(?:\s*-?\s*non-Annotated)?\s*)+)",
    re.I,
)

# A paragraph that is only a callout title ("Tip", "Info"...). It becomes
# "**Tip:**" so the meaning of the callout stays inside the text.
ADMONITION_RE = re.compile(
    r"(Note|Tip|Info|Warning|Check|Danger|Technical Details|Very Technical Details)"
)

# " - FastAPI" suffix that the site adds to every page title
SITE_SUFFIX_RE = re.compile(r"\s*[-|–]\s*FastAPI\s*$", re.I)

# Opening code fence with a language label, e.g. "```python" (maybe indented)
FENCE_LANG_RE = re.compile(r"^\s*```([\w+#.-]+)\s*$", re.M)

# Alternative names for the same language
LANGUAGE_ALIASES = {
    "py": "python", "python3": "python", "py3": "python",
    "sh": "bash", "shell": "bash", "zsh": "bash",
    "js": "javascript", "ts": "typescript", "yml": "yaml",
    "txt": "text", "plaintext": "text",
}


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def sha(text: str, length: int = 16) -> str:
    """
    Return a short, stable SHA-256 hex digest of a string.

    Used for ids and for detecting duplicate content.

    Args:
        text: Any string.
        length: Number of hex characters to keep.

    Returns:
        The first ``length`` characters of the SHA-256 hex digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def normalize_unicode(text: str) -> str:
    """
    Normalize unicode and remove invisible characters.

    NFC normalization makes visually identical characters byte-identical.
    Non-breaking spaces become normal spaces; zero-width characters and soft
    hyphens are removed; line endings become ``\\n``.

    Args:
        text: Raw text.

    Returns:
        The normalized text.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff\u00ad]", "", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def slugify(heading: str) -> str:
    """
    Build the anchor slug MkDocs uses for a heading.

    Example: ``"Create your data model"`` -> ``"create-your-data-model"``.
    Appending ``#slug`` to a page URL links straight to that section, which is
    useful for citations in a RAG answer.

    Args:
        heading: Heading text.

    Returns:
        A lowercase, hyphen-separated slug (may be empty).
    """
    slug = unicodedata.normalize("NFKD", heading).lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"\s+", "-", slug).strip("-")


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


def load_pages(path: Path) -> Iterator[dict]:
    """
    Read the crawler's JSONL file one page at a time.

    Args:
        path: Path to ``pages.jsonl``.

    Yields:
        One dict per page with the keys ``url``, ``title`` and ``markdown``.

    Raises:
        FileNotFoundError: If the crawler output does not exist yet.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run the crawler first.")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# ---------------------------------------------------------------------------
# Per-section collector for links and images
# ---------------------------------------------------------------------------

@dataclass
class Ctx:
    """
    Collects the links and images found while rendering one section.

    Attributes:
        page_url: URL of the page, used to turn relative URLs into absolute ones.
        links: Link metadata found so far.
        images: Image metadata found so far.
    """

    page_url: str
    links: list[dict] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)


def classify_link(href: str) -> str:
    """
    Classify a link target.

    Args:
        href: Absolute URL or ``mailto:`` address.

    Returns:
        ``"email"``, ``"internal"`` (same docs domain) or ``"external"``.
    """
    if href.startswith("mailto:"):
        return "email"
    return "internal" if urlparse(href).netloc.endswith(DOCS_DOMAIN) else "external"


def record_link(ctx: Ctx, label: str, href: str) -> None:
    """
    Store one link in the section metadata.

    In-page anchors (``#section``), empty targets and ``javascript:`` / ``data:``
    URLs are ignored (the link text still stays in the body).

    Args:
        ctx: Collector of the current section.
        label: Plain link text.
        href: Link target as written in the markdown.
    """
    if not href or href.startswith("#") or href.lower().startswith(("javascript:", "data:")):
        return
    absolute = href if href.startswith("mailto:") else urljoin(ctx.page_url, href)
    ctx.links.append({"text": label, "url": absolute, "type": classify_link(absolute)})


def record_image(ctx: Ctx, alt: str, src: str) -> str:
    """
    Store one image in the section metadata and return its text replacement.

    Embedded ``data:`` images are dropped. Images without alt text (usually
    decoration or badges) are recorded but leave nothing in the body.

    Args:
        ctx: Collector of the current section.
        alt: Alt text of the image.
        src: Image source as written in the markdown.

    Returns:
        ``"(Image: alt)"`` when there is alt text, otherwise an empty string.
    """
    alt = alt.strip()
    if not src or src.startswith("data:"):
        return ""
    ctx.images.append({"alt": alt, "src": urljoin(ctx.page_url, src)})
    return f"(Image: {alt})" if alt else ""


def image_from_html_tag(tag: str, ctx: Ctx) -> str:
    """
    Handle a raw HTML ``<img ...>`` tag the same way as a markdown image.

    Args:
        tag: The full ``<img ...>`` tag text.
        ctx: Collector of the current section.

    Returns:
        The text replacement from :func:`record_image`.
    """
    alt = HTML_ATTR_ALT_RE.search(tag)
    src = HTML_ATTR_SRC_RE.search(tag)
    return record_image(ctx, alt.group(1) if alt else "", src.group(1) if src else "")


# ---------------------------------------------------------------------------
# Rendering markdown tokens back into clean markdown
# ---------------------------------------------------------------------------

def find_close(tokens: list[Token], i: int) -> int:
    """
    Find the index of the closing token that matches the opening token ``i``.

    In markdown-it, an opening token has ``nesting == 1`` and its closing token
    has ``nesting == -1`` at the same ``level``.

    Args:
        tokens: Flat token list.
        i: Index of an opening token.

    Returns:
        Index of the matching closing token (the last token if none is found).
    """
    level = tokens[i].level
    for j in range(i + 1, len(tokens)):
        if tokens[j].nesting == -1 and tokens[j].level == level:
            return j
    return len(tokens) - 1


def render_inline(token: Token, ctx: Ctx) -> str:
    """
    Render an ``inline`` token (the content of a paragraph, heading, cell...).

    Text and `inline code` are kept, bold/italic marks are kept, links are
    replaced by their label and images by ``(Image: alt)``. Links and images
    are recorded in ``ctx``. Permalink anchors are removed completely.

    Args:
        token: A token of type ``inline`` (it has ``children``).
        ctx: Collector of the current section.

    Returns:
        The rendered text.
    """
    parts: list[str] = []
    link_stack: list[tuple[str, int]] = []  # (href, index in parts where the label starts)

    for child in token.children or []:
        kind = child.type

        if kind == "text":
            # Attribute lists are removed from text only, never from `code`
            parts.append(ATTR_LIST_RE.sub("", child.content))
        elif kind == "code_inline":
            parts.append(f"`{child.content}`")
        elif kind == "softbreak":
            parts.append(" ")        # a wrapped line inside a paragraph
        elif kind == "hardbreak":
            parts.append("\n")
        elif kind in ("strong_open", "strong_close"):
            parts.append("**")
        elif kind in ("em_open", "em_close"):
            parts.append("*")
        elif kind in ("s_open", "s_close"):
            parts.append("~~")
        elif kind == "image":
            parts.append(record_image(ctx, child.content, child.attrGet("src") or ""))
        elif kind == "html_inline":
            if HTML_BR_RE.fullmatch(child.content.strip()):
                parts.append("\n")
            elif child.content.lower().startswith("<img"):
                parts.append(image_from_html_tag(child.content, ctx))
            # any other inline tag is dropped; its inner text arrives as text tokens
        elif kind == "link_open":
            link_stack.append((child.attrGet("href") or "", len(parts)))
        elif kind == "link_close" and link_stack:
            href, start = link_stack.pop()
            label = re.sub(r"[`*~]", "", "".join(parts[start:])).strip()
            if label in PERMALINK_LABELS:
                del parts[start:]            # permalink anchor: remove it entirely
            else:
                record_link(ctx, label, href)  # keep the label text in the body

    return "".join(parts).replace("¶", "")


def clean_paragraph(text: str) -> str:
    """
    Remove boilerplate paragraphs and mark callout titles.

    Args:
        text: Rendered paragraph text.

    Returns:
        ``""`` for boilerplate (site chrome, "Python 3.10+" labels), the
        callout title as ``"**Tip:**"``, or the original text.
    """
    stripped = text.strip()
    if not stripped or BOILERPLATE_RE.fullmatch(stripped):
        return ""
    if ADMONITION_RE.fullmatch(stripped):
        return f"**{stripped}:**"
    return stripped


def detect_language(code: str, declared: str = "") -> str:
    """
    Decide the language label for a code block.

    Uses the declared language when present (after alias normalization).
    Otherwise makes a light guess: shell commands, JSON, Python or HTML,
    falling back to ``"text"``.

    Args:
        code: The code content.
        declared: Language from the fence line (may be empty).

    Returns:
        A lowercase language name.
    """
    if declared:
        return LANGUAGE_ALIASES.get(declared, declared)

    snippet = code.strip()
    if re.match(
        r"^(\$\s|pip3? |uv |npm |fastapi |uvicorn |docker |curl |git |cd |export |python3? -m )",
        snippet,
    ):
        return "bash"
    if snippet[:1] in "{[":
        try:
            json.loads(snippet)
            return "json"
        except ValueError:
            pass
    if re.search(
        r"^\s*(from\s+\S+\s+import|import\s+\S+|def\s+\w+\(|async\s+def|class\s+\w+|@\w+)",
        snippet,
        re.M,
    ):
        return "python"
    if snippet.startswith("<") and snippet.endswith(">"):
        return "html"
    return "text"


def render_fence(token: Token) -> str:
    """
    Render a code token as a clean fenced block WITHOUT changing the code.

    Only invisible problems are fixed: common indentation is removed, trailing
    spaces are stripped and leading/trailing blank lines are dropped.

    Args:
        token: A ``fence`` or ``code_block`` token.

    Returns:
        The fenced block, or ``""`` if the code is empty.
    """
    code = textwrap.dedent(normalize_unicode(token.content))
    code = "\n".join(line.rstrip() for line in code.split("\n")).strip("\n")
    if not code.strip():
        return ""

    # The info string may look like: python | {.python hl_lines="3"} | py title="a.py"
    info = token.info.strip().lstrip("{").lstrip(".") if token.type == "fence" else ""
    declared = re.split(r"[\s}]", info)[0].lower() if info else ""
    return f"```{detect_language(code, declared)}\n{code}\n```"


def render_html_block(raw: str, ctx: Ctx) -> str:
    """
    Reduce a raw HTML block to plain text.

    ``<img>`` tags are recorded as images, every other tag is removed and its
    inner text is kept.

    Args:
        raw: The HTML block source.
        ctx: Collector of the current section.

    Returns:
        The plain text (may be empty).
    """
    text = HTML_IMG_RE.sub(lambda m: image_from_html_tag(m.group(0), ctx), raw)
    text = HTML_BR_RE.sub("\n", text)
    return HTML_ANY_TAG_RE.sub("", text).strip()


def render_list(open_token: Token, inner: list[Token], ctx: Ctx) -> str:
    """
    Render a bullet or numbered list (nested lists and code included).

    Args:
        open_token: The ``bullet_list_open`` / ``ordered_list_open`` token.
        inner: Tokens between the list's opening and closing tokens.
        ctx: Collector of the current section.

    Returns:
        The list as markdown, with nested content indented under its marker.
    """
    ordered = open_token.type == "ordered_list_open"
    number = int(open_token.attrGet("start") or 1)  # numbered lists may start above 1
    lines: list[str] = []

    i = 0
    while i < len(inner):
        if inner[i].type != "list_item_open":
            i += 1
            continue
        j = find_close(inner, i)
        body = "\n".join(render_blocks(inner[i + 1:j], ctx))

        marker = f"{number}. " if ordered else "- "
        pad = " " * len(marker)
        body_lines = body.split("\n")
        lines.append(marker + body_lines[0])
        lines.extend(pad + line if line else line for line in body_lines[1:])

        number += 1
        i = j + 1
    return "\n".join(lines)


def render_table(inner: list[Token], ctx: Ctx) -> str:
    """
    Render a table as a markdown pipe table.

    The first row is treated as the header row.

    Args:
        inner: Tokens between ``table_open`` and ``table_close``.
        ctx: Collector of the current section.

    Returns:
        The table as markdown, or ``""`` if it has no rows.
    """
    rows: list[list[str]] = []
    row: list[str] | None = None

    for token in inner:
        if token.type == "tr_open":
            row = []
        elif token.type == "inline" and row is not None:
            row.append(render_inline(token, ctx).replace("|", "\\|").replace("\n", " "))
        elif token.type == "tr_close" and row is not None:
            rows.append(row)
            row = None

    if not rows:
        return ""
    header = "| " + " | ".join(rows[0]) + " |"
    divider = "| " + " | ".join(["---"] * len(rows[0])) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join([header, divider, *body])


def render_blocks(tokens: list[Token], ctx: Ctx) -> list[str]:
    """
    Render a sequence of sibling block tokens into a list of markdown blocks.

    Handles paragraphs, lists, tables, block quotes, code, raw HTML and nested
    headings (which become bold lines). Thematic breaks are dropped.

    Args:
        tokens: Block tokens (as a slice of the flat token list).
        ctx: Collector of the current section.

    Returns:
        Rendered, non-empty blocks in document order.
    """
    out: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.nesting == 1:  # an opening token: handle everything up to its close
            j = find_close(tokens, i)
            inner = tokens[i + 1:j]

            if token.type == "paragraph_open":
                if inner and inner[0].type == "inline":
                    text = clean_paragraph(render_inline(inner[0], ctx))
                    if text:
                        out.append(text)
            elif token.type in ("bullet_list_open", "ordered_list_open"):
                text = render_list(token, inner, ctx)
                if text:
                    out.append(text)
            elif token.type == "table_open":
                text = render_table(inner, ctx)
                if text:
                    out.append(text)
            elif token.type == "blockquote_open":
                quote = "\n\n".join(render_blocks(inner, ctx))
                if quote:
                    out.append("\n".join(f"> {l}" if l else ">" for l in quote.split("\n")))
            elif token.type == "heading_open":
                # A heading inside a list or quote: keep it as a bold line
                if inner and inner[0].type == "inline":
                    out.append(f"**{render_inline(inner[0], ctx).strip()}**")
            else:
                out.extend(render_blocks(inner, ctx))  # any other container
            i = j + 1

        else:  # a single token (no children block)
            if token.type in ("fence", "code_block"):
                block = render_fence(token)
                if block:
                    out.append(block)
            elif token.type == "html_block":
                text = render_html_block(token.content, ctx)
                if text:
                    out.append(text)
            i += 1
    return out


# ---------------------------------------------------------------------------
# Splitting a page into sections
# ---------------------------------------------------------------------------

def clean_heading(text: str) -> str:
    """
    Turn rendered heading text into plain text.

    Removes bold/italic/code marks and permalink characters.

    Args:
        text: Heading text rendered by :func:`render_inline`.

    Returns:
        Plain heading text, e.g. ``"Create your data model"``.
    """
    return re.sub(r"[`*~]+", "", text).replace("¶", "").strip()


def parse_sections(markdown: str, page_url: str) -> list[dict]:
    """
    Parse page markdown into sections, one per heading.

    A stack of the currently open headings gives every section its full path
    (for example an H3 under an H2 under an H1 gets three entries). Text before
    the first heading becomes an intro section with an empty path. Duplicate
    code blocks inside one section are kept once.

    Args:
        markdown: Page markdown from the crawler.
        page_url: URL of the page, used to resolve relative links and images.

    Returns:
        A list of dicts: ``heading_path``, ``level``, ``text``, ``links``,
        ``images``. Sections without any text are omitted.
    """
    tokens = MD.parse(normalize_unicode(markdown))

    def new_section(path: list[str], level: int) -> dict:
        return {
            "heading_path": path, "level": level,
            "blocks": [], "seen_code": set(), "ctx": Ctx(page_url),
        }

    stack: list[tuple[int, str]] = []  # (level, heading text) of open headings
    current = new_section([], 0)
    sections = [current]

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # --- A heading starts a new section ---------------------------------
        if token.type == "heading_open":
            level = int(token.tag[1])  # "h2" -> 2
            heading = clean_heading(render_inline(tokens[i + 1], Ctx(page_url)))

            # Close deeper-or-equal headings, then open the new one
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, heading))

            current = new_section([h for _, h in stack], level)
            sections.append(current)
            i += 3  # heading_open, inline, heading_close
            continue

        # --- Anything else is content of the current section ----------------
        if token.nesting == 1:
            j = find_close(tokens, i)
            chunk = tokens[i:j + 1]
            i = j + 1
        else:
            chunk = [token]
            i += 1

        for block in render_blocks(chunk, current["ctx"]):
            if block.startswith("```"):          # skip duplicated code variants
                if block in current["seen_code"]:
                    continue
                current["seen_code"].add(block)
            current["blocks"].append(block)

    # --- Finalize: join blocks into text, drop empty sections ----------------
    result = []
    for sec in sections:
        text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(sec["blocks"])).strip()
        if not text:
            continue  # empty section: its children still carry the heading path
        result.append(
            {
                "heading_path": sec["heading_path"],
                "level": sec["level"],
                "text": text,
                "links": unique_by(sec["ctx"].links, "url"),
                "images": unique_by(sec["ctx"].images, "src"),
            }
        )
    return result


# ---------------------------------------------------------------------------
# Page-level metadata and the final records
# ---------------------------------------------------------------------------

def get_category(url: str) -> str:
    """
    Derive a category from the first URL path segment.

    Examples: ``/tutorial/body/`` -> ``"tutorial"``, ``/`` -> ``"home"``.
    Useful as a metadata filter at retrieval time.

    Args:
        url: Page URL.

    Returns:
        The first path segment, or ``"home"`` for the root page.
    """
    segments = [s for s in urlparse(url).path.split("/") if s]
    return segments[0] if segments else "home"


def get_page_title(raw_title: str, sections: list[dict]) -> str:
    """
    Pick a clean page title.

    Removes the " - FastAPI" suffix. If the title is empty, falls back to the
    first heading on the page.

    Args:
        raw_title: Title captured by the crawler.
        sections: Parsed sections of the page.

    Returns:
        The page title (empty string if nothing is available).
    """
    title = SITE_SUFFIX_RE.sub("", normalize_unicode(raw_title or "")).strip()
    if title:
        return title
    for sec in sections:
        if sec["heading_path"]:
            return sec["heading_path"][0]
    return ""


def process_page(page: dict) -> tuple[list[dict], bool]:
    """
    Convert one crawled page into a list of section records.

    Args:
        page: ``{"url": str, "title": str, "markdown": str}``.

    Returns:
        ``(records, had_headings)``. ``records`` is empty if the page has
        almost no content. ``had_headings`` is False when no heading was found,
        which can mean the crawled markdown looks different than expected.
    """
    url = page["url"]
    sections = parse_sections(page.get("markdown", ""), url)
    had_headings = any(sec["heading_path"] for sec in sections)

    page_title = get_page_title(page.get("title", ""), sections)
    doc_id = sha(url, 12)
    category = get_category(url)

    records: list[dict] = []
    for sec in sections:
        path = sec["heading_path"]
        anchor = slugify(path[-1]) if path else ""

        # Breadcrumb for embeddings: "Page title > H2 > H3" (no repeated titles)
        breadcrumb = " > ".join(dict.fromkeys([page_title, *path]))

        # Code languages come straight from the fences in the final text
        languages = FENCE_LANG_RE.findall(sec["text"])

        records.append(
            {
                "doc_id": doc_id,
                "section_id": f"{doc_id}-{len(records):03d}",
                "url": url,
                "section_url": f"{url}#{anchor}" if anchor else url,
                "page_title": page_title,
                "category": category,
                "heading_path": path,
                "heading_level": sec["level"],
                "text": sec["text"],
                # Same text with its breadcrumb on top: embed THIS field
                "contextual_text": f"{breadcrumb}\n\n{sec['text']}",
                "has_code": bool(languages),
                "code_languages": sorted(set(languages)),
                "code_block_count": len(languages),
                "word_count": len(sec["text"].split()),
                "links": sec["links"],
                "images": sec["images"],
                "content_hash": sha(sec["text"]),
            }
        )

    # Drop pages that ended up (almost) empty after cleaning
    if sum(r["word_count"] for r in records) < MIN_PAGE_WORDS:
        return [], had_headings
    return records, had_headings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Parse every crawled page, write the sections to disk and print a report.

    The report helps you sanity-check the result: pages and sections produced,
    code languages found, and pages where no headings were detected (if that
    number is high, inspect the raw markdown of those pages).
    """
    pages_in = pages_out = sections_out = 0
    no_heading_pages = 0
    languages: Counter = Counter()
    categories: Counter = Counter()
    link_count = image_count = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        for page in load_pages(INPUT_PATH):
            pages_in += 1
            records, had_headings = process_page(page)

            if not had_headings:
                no_heading_pages += 1
            if not records:
                continue

            pages_out += 1
            for rec in records:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                sections_out += 1
                languages.update(rec["code_languages"])
                categories[rec["category"]] += 1
                link_count += len(rec["links"])
                image_count += len(rec["images"])

    print(f"Pages read:             {pages_in}")
    print(f"Pages kept:             {pages_out}")
    print(f"Sections written:       {sections_out}")
    print(f"Pages with no headings: {no_heading_pages}")
    print(f"Links / images found:   {link_count} / {image_count}")
    print(f"Sections by category:   {dict(categories)}")
    print(f"Code languages:         {dict(languages)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()