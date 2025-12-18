import requests
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
import markdownify
import time
import json

# ---------------- CONFIG ----------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ✅ FIXED PATH (ONLY CHANGE)
OUTPUT_ROOT = Path(
    "GitBook_Content/Influencers/Game Design - Product - Production"
)

CACHE_FILE = OUTPUT_ROOT / ".authors_cache.json"

AUTHORS = {
    "Anton Slashcev": "https://www.gamigion.com/author/antonslashcev/",
    "Sergei Zenkin": "https://www.gamigion.com/author/sergeizenkin/",
    "Ali Farha": "https://www.gamigion.com/author/alifarha/",
    "Jakub Remiar": "https://www.gamigion.com/author/jakubremiar/",
    "Ahmetcan Demirel": "https://www.gamigion.com/author/ahmetcandemirel/",
}

# ---------------- UTIL ----------------
def safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in " -_")[:150]


def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def get_html(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.text
    except requests.RequestException:
        pass
    return None


# ---------------- LINK EXTRACTION (UNCHANGED) ----------------
def extract_post_links(author_url):
    page = 1
    links = []

    while True:
        url = author_url.rstrip("/")
        if page > 1:
            url = f"{url}/page/{page}/"

        html = get_html(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("article")

        if not articles:
            break

        for art in articles:
            a = art.find("a", href=True)
            if a:
                full = a["href"].split("#")[0]
                if full not in links:
                    links.append(full)

        page += 1
        time.sleep(0.1)

    return links


# ---------------- CONTENT EXTRACTION (UNCHANGED) ----------------
def extract_full_article(url):
    html = get_html(url)
    if not html:
        return None, None, None

    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("meta", {"property": "og:title"}) or soup.find("h1")
    title = (
        title_tag["content"]
        if title_tag and title_tag.get("content")
        else title_tag.text.strip()
    )

    content = (
        soup.find("div", {"class": "typify-entrycontent"})
        or soup.find("article")
        or soup.find("main")
    )

    if not content:
        return title, None, None

    markdown_body = markdownify.markdownify(str(content))
    h = hashlib.sha256(html.encode()).hexdigest()

    return title, markdown_body, h


# ---------------- SAVE MARKDOWN ----------------
def save_markdown(folder: Path, index: int, title: str, md: str):
    filename = f"{index:03d}_{safe_filename(title)}.md"
    path = folder / filename
    path.write_text(f"# {title}\n\n{md}", encoding="utf-8")
    return filename


# ---------------- SCRAPE AUTHOR ----------------
def scrape_author(name, url, cache):
    print(f"\n▶ START: {name}")

    folder = OUTPUT_ROOT / name.replace(" ", "")
    folder.mkdir(parents=True, exist_ok=True)

    links = extract_post_links(url)
    print(f"Collected {len(links)} posts")

    for idx, post_url in enumerate(links, start=1):
        html = get_html(post_url)
        if not html:
            continue

        h = hashlib.sha256(html.encode()).hexdigest()
        if post_url in cache and cache[post_url]["hash"] == h:
            print(f" unchanged: {idx:03d}")
            continue

        title, md, hash_value = extract_full_article(post_url)
        if not md:
            print(f" skipped (no content)")
            continue

        fname = save_markdown(folder, idx, title, md)
        cache[post_url] = {"hash": hash_value, "file": fname}
        print(f" saved: {idx:03d}")


# ---------------- MAIN ----------------
def main():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    cache = load_cache()

    for name, url in AUTHORS.items():
        scrape_author(name, url, cache)

    save_cache(cache)
    print("\n🎉 DONE — All authors scraped successfully")


if __name__ == "__main__":
    main()
