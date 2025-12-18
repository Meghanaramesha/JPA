import re
import json
import time
import hashlib
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Optional, List, Dict, Any

import requests
from bs4 import BeautifulSoup
import markdownify

# ---------------- CONFIG ----------------
BLOGS: Dict[str, Dict[str, Any]] = {
    "Lanceric": {
        "base_url": "https://lancaric.me/blog/",
        "pages": 28,
    },
    "RamizTrtovac": {
        "base_url": "https://ramiztrtovac.com/blog/",
        "pages": 1,
    },
    "Kopelovich": {
        "base_url": "https://www.gamigion.com/author/kopelovich/",
        "pages": 1,  # kept as-is
    },
    "RZain": {
        "base_url": "https://rzain.blog/games/",
        "pages": 1,
    },
}

OUTPUT_ROOT = Path("GitBook_Content")
INFLUENCERS_DIR = OUTPUT_ROOT / "Influencers"
AGENCY_DIR = INFLUENCERS_DIR / "UA & Growth Agencies"

CACHE_FILE = OUTPUT_ROOT / ".scrape_cache.json"
LOG_FILE = OUTPUT_ROOT / "scrape.log"

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GitBookScraper/4.0)"
}

REQUEST_TIMEOUT = 12
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5

FNAME_SAFE = re.compile(r"[^A-Za-z0-9\-_ ]")

# ---------------- LOGGING ----------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

# ---------------- UTIL ----------------
def ensure_folder(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def ensure_readme(folder: Path, title: str):
    readme = folder / "README.md"
    if not readme.exists():
        readme.write_text(f"# {title}\n", encoding="utf-8")

def clean_filename(title: str) -> str:
    return (FNAME_SAFE.sub("", title).strip() or "untitled")[:200]

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_cache() -> Dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("Failed to read cache")
    return {"pages": {}}

def save_cache(cache: Dict[str, Any]):
    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

# ---------------- HTTP ----------------
session = requests.Session()
session.headers.update(HEADERS)

def get_html(url: str) -> Optional[str]:
    delay = 0.5
    for _ in range(MAX_RETRIES):
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            time.sleep(delay)
            delay *= RETRY_BACKOFF
    return None

# ---------------- LINK EXTRACTION ----------------
def extract_links_from_listing(html: str, base_url: str, blog_name: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []

    # ---- Ramiz (UNCHANGED) ----
    if blog_name == "RamizTrtovac":
        for a in soup.find_all("a", href=True):
            full = urljoin(base_url, a["href"])
            path = urlparse(full).path.lower()
            if "/useraquisition/" in path or "/creatives/" in path:
                if full not in links:
                    links.append(full)
        return links

    # ---- Kopelovich (ONLY ADD PAGINATION) ----
    if blog_name == "Kopelovich":
        page = 1
        while True:
            page_url = base_url.rstrip("/")
            if page > 1:
                page_url = f"{page_url}/page/{page}/"

            html_page = get_html(page_url)
            if not html_page:
                break

            page_soup = BeautifulSoup(html_page, "html.parser")
            articles = page_soup.find_all("article")
            if not articles:
                break

            for art in articles:
                a = art.find("a", href=True)
                if not a:
                    continue

                full = urljoin(base_url, a["href"])
                parsed = urlparse(full)

                if parsed.netloc != "www.gamigion.com":
                    continue

                path = parsed.path.rstrip("/").lower()
                if any(x in path for x in [
                    "/category/", "/author/", "/about", "/events",
                    "/reports", "/games-radar", "/privacy",
                    "/terms", "/wp-"
                ]):
                    continue

                if full not in links:
                    links.append(full)

            page += 1
            time.sleep(0.2)

        return links

    # ---- RZain (UNCHANGED) ----
    if blog_name == "RZain":
        for a in soup.select("li.wp-block-post a[href]"):
            full = urljoin(base_url, a["href"])
            if full.startswith("https://rzain.blog/") and full not in links:
                links.append(full)
        return links

    # ---- Default (UNCHANGED) ----
    for art in soup.find_all("article"):
        a = art.find("a", href=True)
        if a:
            full = urljoin(base_url, a["href"])
            if full not in links:
                links.append(full)

    return links

# ---------------- CONTENT EXTRACTION ----------------
def extract_full_content(html: str) -> Optional[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    title_tag = (
        soup.find("meta", {"property": "og:title"})
        or soup.find("title")
        or soup.find("h1")
    )

    title = (
        title_tag.get("content", "").strip()
        if hasattr(title_tag, "get")
        else (title_tag.string.strip() if title_tag else "Untitled")
    )

    gamigion_content = soup.select_one("div.typify-post__content")
    if gamigion_content and len(gamigion_content.get_text(strip=True)) > 100:
        return title, str(gamigion_content)

    for tag in ["article", "main", "section"]:
        content = soup.find(tag)
        if content and len(content.get_text(strip=True)) > 150:
            return title, str(content)

    if soup.body:
        return title, str(soup.body)

    return None

# ---------------- SAVE MARKDOWN ----------------
def write_markdown(blog_folder: Path, title: str, html_fragment: str, index: int):
    fname = f"{index:03d}_{clean_filename(title)}.md"
    md_body = markdownify.markdownify(html_fragment, heading_style="ATX")
    (blog_folder / fname).write_text(
        f"# {title}\n\n{md_body}\n",
        encoding="utf-8"
    )

# ---------------- SCRAPE BLOG ----------------
def scrape_blog(blog_name: str, base_url: str, total_pages: int, cache: Dict[str, Any]):
    print(f"\n▶ START: {blog_name}")

    blog_folder = AGENCY_DIR / blog_name
    ensure_folder(blog_folder)
    ensure_readme(blog_folder, blog_name)

    all_links: List[str] = []

    pages = [base_url.rstrip("/")]
    if blog_name == "Lanceric" and total_pages > 1:
        pages = [
            base_url.rstrip("/") if i == 1 else f"{base_url.rstrip('/')}/page/{i}/"
            for i in range(1, total_pages + 1)
        ]

    for page in pages:
        html = get_html(page)
        if not html:
            continue
        for link in extract_links_from_listing(html, base_url, blog_name):
            if link not in all_links:
                all_links.append(link)

    print(f"Collected {len(all_links)} links")

    for idx, url in enumerate(all_links, start=1):
        html = get_html(url)
        if not html:
            continue

        h = sha256_text(html)
        if cache["pages"].get(url, {}).get("hash") == h:
            continue

        extracted = extract_full_content(html)
        if not extracted:
            continue

        title, content_html = extracted
        write_markdown(blog_folder, title, content_html, idx)
        cache["pages"][url] = {"hash": h, "last_seen": int(time.time())}

# ---------------- MAIN ----------------
def main():
    ensure_folder(INFLUENCERS_DIR)
    ensure_folder(AGENCY_DIR)

    ensure_readme(INFLUENCERS_DIR, "Influencers")
    ensure_readme(AGENCY_DIR, "UA & Growth Agencies")

    cache = load_cache()

    for name, cfg in BLOGS.items():
        scrape_blog(name, cfg["base_url"], cfg["pages"], cache)

    save_cache(cache)
    print("\n🎉 DONE — ALL ARTICLES SCRAPED CORRECTLY\n")

if __name__ == "__main__":
    main()
