"""
FastAPI Docs Crawler (Crawl4AI + sitemap)
=========================================

Crawls the official FastAPI documentation (https://fastapi.tiangolo.com) and
saves every English page as clean markdown, ready for a RAG pipeline
(chunking -> embeddings -> vector database).

Why the sitemap?
----------------
Following links page by page can miss pages (it depends on which links the
crawler can see). MkDocs sites publish a ``sitemap.xml`` that lists every
page, so we read that list and crawl those URLs directly. This gives full,
predictable coverage.

How it works
------------
1. Download ``sitemap.xml`` and keep only the English page URLs.
2. Crawl all those URLs concurrently with Crawl4AI (``arun_many``).
3. Keep only the main article content of each page (no nav bars / footers).
4. Save the results to disk:

        <project root>/data/fastapi_docs/
            pages/<slug>.md    one markdown file per page
            pages.jsonl        one JSON record per line (url, title, markdown)

Setup (once)
------------
    uv add crawl4ai
    uv run crawl4ai-setup        # downloads the Chromium browser used by Playwright

Run
---
    uv run python .\\test_crawler.py
"""

import asyncio
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

# ---------------------------------------------------------------------------
# Settings (change these to control the crawl)
# ---------------------------------------------------------------------------

# Sitemap listing every page of the documentation.
SITEMAP_URL = "https://fastapi.tiangolo.com/sitemap.xml"

# Where results are stored. This file lives in <project>/app/ingestion/, so
# parents[2] is the project root. Output goes to <project>/data/fastapi_docs/.
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "fastapi_docs"
PAGES_DIR = OUTPUT_DIR / "pages"          # one .md file per page
JSONL_PATH = OUTPUT_DIR / "pages.jsonl"   # all pages in one JSONL file

# The FastAPI docs are translated into many languages under /<lang>/ (for
# example /es/tutorial/). The English docs live at the site root, so any path
# starting with /xx/ or /xx-yy/ is treated as a translation and skipped.
TRANSLATION_RE = re.compile(r"^/[a-z]{2}(-[a-z]+)?/")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_english_doc(url: str) -> bool:
    """
    Check whether a URL points to the English (non-translated) docs.

    Translated pages have a language prefix in the path, for example
    ``/es/tutorial/`` or ``/zh-hant/advanced/``. English pages do not.

    Args:
        url: Full page URL, e.g. ``https://fastapi.tiangolo.com/tutorial/``.

    Returns:
        True for English pages, False for translated pages.
    """
    path = urlparse(url).path  # e.g. "/es/tutorial/"
    return TRANSLATION_RE.match(path) is None


def url_to_slug(url: str) -> str:
    """
    Convert a page URL into a safe file name (without extension).

    Examples:
        https://fastapi.tiangolo.com/                 -> "index"
        https://fastapi.tiangolo.com/tutorial/body/   -> "tutorial__body"

    Args:
        url: Full page URL.

    Returns:
        A string containing only letters, digits, ``_`` and ``-``, which is
        safe to use as a file name on Windows, macOS and Linux.
    """
    path = urlparse(url).path.strip("/")
    if not path:
        return "index"  # the home page has an empty path
    # "/" becomes "__"; any other unsafe character becomes "_"
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", path.replace("/", "__"))


def get_markdown(result) -> str:
    """
    Safely extract the markdown text from a Crawl4AI result object.

    In recent Crawl4AI versions ``result.markdown`` is a string-like object
    that also exposes ``.raw_markdown`` (full markdown) and ``.fit_markdown``
    (filtered markdown). Older versions return a plain string. This helper
    handles both cases.

    Args:
        result: A ``CrawlResult`` returned by the crawler.

    Returns:
        The page markdown, or an empty string if nothing was produced.
    """
    md = result.markdown
    if not md:
        return ""
    return getattr(md, "raw_markdown", None) or str(md)


def get_urls_from_sitemap(sitemap_url: str = SITEMAP_URL) -> list[str]:
    """
    Download the site's ``sitemap.xml`` and return all English page URLs.

    MkDocs generates a sitemap that lists every page of the documentation,
    including all translations. This function keeps only the English pages.

    Args:
        sitemap_url: URL of the sitemap.xml file.

    Returns:
        A de-duplicated list of English page URLs, in sitemap order.
    """
    # Some servers reject requests that have no User-Agent header
    request = urllib.request.Request(sitemap_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)

    # Sitemap tags are namespaced, so match any tag whose name ends with "loc"
    urls = [el.text.strip() for el in root.iter() if el.tag.endswith("loc") and el.text]

    # Keep English pages only; dict.fromkeys removes duplicates, keeps order
    return list(dict.fromkeys(u for u in urls if is_english_doc(u)))

def save_page(page: dict, jsonl_file) -> None:
    """
    Save one crawled page to disk in two formats.

    1. ``pages/<slug>.md``: a readable markdown file with the title and the
        source URL at the top.
    2. One line appended to ``pages.jsonl``: handy for loading all pages at
        once in the next pipeline step.

    Args:
        page: Dict with the keys ``url``, ``title`` and ``markdown``.
        jsonl_file: An open, writable file handle for ``pages.jsonl``.
    """
    slug = url_to_slug(page["url"])

    # Markdown file: title + source link, then the page content
    md_text = f"# {page['title']}\n\nSource: {page['url']}\n\n{page['markdown']}"
    (PAGES_DIR / f"{slug}.md").write_text(md_text, encoding="utf-8")

    # JSONL: ensure_ascii=False keeps non-ASCII characters readable
    jsonl_file.write(json.dumps(page, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Core crawling logic
# ---------------------------------------------------------------------------

async def crawl_fastapi_docs() -> dict:
    """
    Crawl every English FastAPI docs page and store the results on disk.

    Steps:
        1. Create the output folders if they do not exist.
        2. Read the page list from the sitemap.
        3. Crawl all pages concurrently and stream the results.
        4. Skip failed or empty pages; save the rest with ``save_page``.

    Returns:
        Counts for the run: {"urls_in_sitemap", "saved", "empty", "failed"}.
    """
    # --- 1. Prepare output folders -----------------------------------------
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    # --- 2. Get the list of pages to crawl ---------------------------------
    urls = get_urls_from_sitemap()
    print(f"Sitemap contains {len(urls)} English pages")

    # --- 3. Crawl configuration --------------------------------------------
    run_config = CrawlerRunConfig(
        # LXML-based HTML parser: fast and reliable for content extraction
        scraping_strategy=LXMLWebScrapingStrategy(),
        # Always fetch fresh content instead of using Crawl4AI's local cache
        cache_mode=CacheMode.BYPASS,
        # Streaming: each page is yielded as soon as it is crawled, so we can
        # save it immediately instead of holding everything in memory
        stream=True,
        # Build the markdown from the <article> element only (the FastAPI docs
        # use the MkDocs Material layout), which drops sidebars and footers
        target_elements=["article"],
        # Remove non-content tags that only add noise
        excluded_tags=["script", "style"],
        # Ignore tiny text blocks (fewer than 10 words)
        word_count_threshold=10,
        # Close cookie banners / popups that could cover the content
        remove_overlay_elements=True,
        verbose=False,
    )

    saved = failed = empty = 0

    # --- 4. Crawl and save --------------------------------------------------
    # The JSONL file stays open during the crawl so each page is appended
    # as soon as it arrives.
    with open(JSONL_PATH, "w", encoding="utf-8") as jsonl_file:
        # "async with" guarantees the browser is closed even on errors
        async with AsyncWebCrawler(
            config=BrowserConfig(headless=True, verbose=False)
        ) as crawler:
            # arun_many crawls the whole URL list concurrently
            async for result in await crawler.arun_many(urls, config=run_config):

                # Pages that failed to load (timeouts, 404s, etc.)
                if not result.success:
                    failed += 1
                    print(f"[FAIL] {result.url} -> {result.error_message}")
                    continue

                # Pages that loaded but produced no usable markdown
                markdown = get_markdown(result)
                if not markdown.strip():
                    empty += 1
                    print(f"[EMPTY] {result.url}")
                    continue

                page = {
                    "url": result.url,
                    "title": (result.metadata or {}).get("title", ""),
                    "markdown": markdown,
                }
                save_page(page, jsonl_file)
                saved += 1
                print(f"[OK] {result.url}")

    print(f"\nDone. saved={saved} empty={empty} failed={failed}")
    print(f"Output folder: {OUTPUT_DIR}")
    return {"urls_in_sitemap": len(urls), "saved": saved, "empty": empty, "failed": failed}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    """
    Run the crawler.

    After this finishes, the next stage of your RAG pipeline can read
    ``data/fastapi_docs/pages.jsonl`` (or the ``.md`` files) and do the
    chunking, embedding and vector-database indexing.
    """
    await crawl_fastapi_docs()


# Only run when executed directly (not when imported from another module).
# asyncio.run() starts the event loop that the async crawler needs.
if __name__ == "__main__":
    asyncio.run(main())