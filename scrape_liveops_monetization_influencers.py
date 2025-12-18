# scrape_liveops_monetization_influencers.py



import re
import time
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import markdownify

# ---------------- CONFIG ----------------
INFLUENCERS = {
    "FelixBraberg_Substack": "https://felixbraberg.substack.com/archive?sort=new",
    "FelixBraberg_Blog": "https://www.felixbraberg.com/blog",
    "SergeiVasiuk": "https://www.gamigion.com/author/sergeivasiuk/",
    "OxanaFomina": "https://www.gamigion.com/author/oxanafomina/",
}

OUTPUT_ROOT = Path("GitBook_Content") / "Influencers" / "Live-Ops & Monetization Experts"
CACHE_FILE = OUTPUT_ROOT / ".scrape_cache.json"
LOG_FILE = OUTPUT_ROOT / "scrape_liveops.log"

HEADERS = {"User-Agent": "Mozilla/5.0"}
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

FNAME_SAFE = re.compile(r"[^A-Za-z0-9\-_ ]")

# ---------------- LOGGING ----------------
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler())

# ---------------- SESSION ----------------
session = requests.Session()
session.headers.update(HEADERS)

# ---------------- UTIL ----------------
def clean_filename(title: str) -> str:
    name = FNAME_SAFE.sub("", title).strip()
    return (name or "untitled")[:180]

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_cache() -> Dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {"pages": {}}

def save_cache(cache: Dict):
    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

def get_html(url: str) -> Optional[str]:
    for _ in range(MAX_RETRIES):
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            time.sleep(1)
    return None

# ---------------- SUBSTACK ----------------
def extract_substack_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if href and "/p/" in href:
            links.append(urljoin(base_url, href).split("#")[0].rstrip("/"))
    return list(dict.fromkeys(links))

# ---------------- BLOG ----------------
def extract_blog_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        full = urljoin(base_url, href)
        if full.startswith(base_url.rstrip("/")):
            links.append(full.rstrip("/"))
    return list(dict.fromkeys(links))

# ---------------- GAMIGION ----------------
def extract_gamigion_links(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for article in soup.find_all("article"):
        a = article.find("a", href=True)
        if not a:
            continue
        href = a["href"].split("#")[0].rstrip("/")
        if (
            href.startswith("https://www.gamigion.com/")
            and "/author/" not in href
            and not href.endswith("/about")
        ):
            links.append(href)
    return links

def gamigion_next_page(html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    nxt = soup.find("link", rel="next")
    if nxt and nxt.get("href"):
        return urljoin(base_url, nxt["href"])
    return None

# ---------------- CONTENT ----------------
def extract_content(html: str) -> Optional[Tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.find("meta", {"property": "og:title"}) or soup.find("h1")
    title = title_el.get("content", "").strip() if hasattr(title_el, "get") else title_el.get_text(strip=True)

    content = (
        soup.find("div", class_="typify-entrycontent")
        or soup.find("article")
        or soup.find("main")
    )

    if not content:
        return None

    md = markdownify.markdownify(str(content), heading_style="ATX")
    return title, md

# ---------------- SAVE ----------------
def save_md(folder: Path, title: str, md: str, url: str, index: int):
    fname = f"{index:03d}_{clean_filename(title)}.md"
    (folder / fname).write_text(
        f"---\noriginal_url: {url}\ntitle: {title}\n---\n\n# {title}\n\n{md}\n",
        encoding="utf-8",
    )
    return fname

# ---------------- SCRAPE ----------------
def scrape_source(name: str, start_url: str, cache: Dict):
    logging.info("▶ START %s", name)
    folder = OUTPUT_ROOT / name
    folder.mkdir(parents=True, exist_ok=True)

    urls = []
    page = start_url.rstrip("/")

    while page:
        html = get_html(page)
        if not html:
            break

        if "substack.com" in page:
            urls.extend(extract_substack_links(html, page))
            break

        if "gamigion.com" in page:
            urls.extend(extract_gamigion_links(html))
            page = gamigion_next_page(html, page)
            continue

        urls.extend(extract_blog_links(html, page))
        break

    urls = list(dict.fromkeys(urls))
    logging.info("%s → %d articles", name, len(urls))

    for idx, url in enumerate(urls, start=1):
        html = get_html(url)
        if not html:
            continue

        h = sha256_text(html)
        if url in cache["pages"] and cache["pages"][url]["hash"] == h:
            continue

        extracted = extract_content(html)
        if not extracted:
            continue

        title, md = extracted
        fname = save_md(folder, title, md, url, idx)

        cache["pages"][url] = {"hash": h, "file": fname}

# ---------------- MAIN ----------------
def main():
    cache = load_cache()

    for name, url in INFLUENCERS.items():
        scrape_source(name, url, cache)
        time.sleep(1)

    save_cache(cache)
    print("🎉 DONE — All Live-Ops & Monetization Influencers scraped correctly")

if __name__ == "__main__":
    main()
