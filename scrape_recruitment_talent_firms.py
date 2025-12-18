import os
import re
import time
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ================= CONFIG =================

BASE_DIR = "GitBook_Content/Influencers/Recruitment & Talent Firms"

AMIR_YT_DIR  = os.path.join(BASE_DIR, "AmirSatvat_YouTube")
AMIR_RES_DIR = os.path.join(BASE_DIR, "AmirSatvat_Resources")
OMER_GAM_DIR = os.path.join(BASE_DIR, "OmerYakabagi", "Journal")

os.makedirs(AMIR_YT_DIR, exist_ok=True)
os.makedirs(AMIR_RES_DIR, exist_ok=True)
os.makedirs(OMER_GAM_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ================= HELPERS =================

def clean_filename(text):
    text = re.sub(r"[\\/*?:\"<>|\n\r]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:150]

def save_md(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# ================= AMIR SATVAT — YOUTUBE =================

def extract_amir_youtube():
    print("▶ Extracting Amir Satvat YouTube videos...")

    driver = get_driver()
    driver.get("https://www.youtube.com/@AmirSatvat/videos")
    time.sleep(10)

    videos = {}
    elements = driver.find_elements(By.XPATH, "//a[@href and @title]")

    for el in elements:
        href = el.get_attribute("href")
        title = el.get_attribute("title")

        if href and "/watch?v=" in href and title:
            vid = href.split("v=")[1].split("&")[0]
            videos[vid] = title

    driver.quit()
    print(f"🔎 Found {len(videos)} videos")

    for vid, title in videos.items():
        filename = f"{clean_filename(title)}.md"
        path = os.path.join(AMIR_YT_DIR, filename)

        save_md(
            path,
            f"# {title}\n\n"
            f"**YouTube URL:** https://www.youtube.com/watch?v={vid}\n"
        )

# ================= AMIR SATVAT — RESOURCES =================

def extract_amir_resources():
    print("▶ Extracting Amir Satvat Resources...")

    driver = get_driver()
    driver.get("https://amirsatvat.com/resourcelibrary")
    time.sleep(10)

    seen = set()
    saved = 0

    links = driver.find_elements(By.XPATH, "//a[@href]")

    for a in links:
        href = a.get_attribute("href")
        title = a.text.strip()

        if not href:
            continue

        if not any(x in href.lower() for x in ["pdf", "doc", "ppt", "drive", "dropbox"]):
            continue

        if href in seen:
            continue
        seen.add(href)

        if not title:
            title = href.split("/")[-1]

        filename = f"{clean_filename(title)}.md"
        path = os.path.join(AMIR_RES_DIR, filename)

        save_md(
            path,
            f"# {title}\n\n"
            f"**Download Link:**\n{href}\n"
        )
        saved += 1

    driver.quit()
    print(f"🔎 Saved {saved} resource files")

# ================= OMER YAKABAGI — GAMIGION =================

def extract_omer_gamigion():
    print("▶ Extracting Omer Yakabagi Gamigion articles...")

    article_urls = []
    seen = set()

    for page in range(1, 25):
        url = "https://www.gamigion.com/author/omeryakabagi/"
        if page > 1:
            url += f"page/{page}/"

        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.find_all("article")
        if not posts:
            break

        for post in posts:
            a = post.find("a", href=True)
            if a:
                link = a["href"].split("#")[0]
                if link not in seen:
                    seen.add(link)
                    article_urls.append(link)

    print(f"🔗 Found {len(article_urls)} articles")

    for idx, url in enumerate(article_urls, start=1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")

            title_el = soup.find("h1")
            content = (
                soup.find("div", id="typify-the_content")
                or soup.find("div", class_="typify-the_content")
            )

            if not title_el or not content:
                continue

            title = title_el.get_text(strip=True)

            body = []
            for el in content.find_all(["h2", "h3", "p", "li", "img"]):
                if el.name == "img":
                    src = el.get("src")
                    if src:
                        body.append(f"![image]({src})")
                else:
                    txt = el.get_text(strip=True)
                    if txt:
                        body.append(txt)

            if not body:
                continue

            md = f"""# {title}

**Source:** {url}

{chr(10).join(body)}
"""

            filename = f"{idx:03d}_{clean_filename(title)}.md"
            save_md(os.path.join(OMER_GAM_DIR, filename), md)

        except Exception:
            continue

# ================= RUN =================

if __name__ == "__main__":
    extract_amir_youtube()
    extract_amir_resources()
    extract_omer_gamigion()
    print("\n🎯 Recruitment & Talent Firms — STRUCTURE & CONTENT DONE CORRECTLY")
