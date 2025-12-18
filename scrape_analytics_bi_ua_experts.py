import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import markdownify
from bs4 import BeautifulSoup

# ================== CONFIG ==================

BASE_DIR = Path("GitBook_Content") / "Influencers" / "Analytics - BI - UA Data Experts"
CARLY_DIR = BASE_DIR / "CarlyTaylor"
PAUL_DIR = BASE_DIR / "PaulLevchuk"

CARLY_DIR.mkdir(parents=True, exist_ok=True)
PAUL_DIR.mkdir(parents=True, exist_ok=True)

CARLY_URL = "https://www.databricks.com/blog/author/carly-taylor"
PAUL_URL = "https://medium.com/@paul.levchuk"

# ================== DRIVER ==================

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def clean(text):
    text = re.sub(r"[\\/*?:\"<>|\n\r]", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:150]

# ================== DATABRICKS ==================

def scrape_carly_taylor():
    print("\n▶ Scraping Carly Taylor (Databricks – WORKING)")

    driver = get_driver()
    driver.get(CARLY_URL)
    time.sleep(6)

    links = []
    for a in driver.find_elements(By.XPATH, "//a[@href]"):
        href = a.get_attribute("href")
        if href and "/blog/" in href and "/author/" not in href and "category" not in href:
            links.append(href.split("?")[0])

    links = list(dict.fromkeys(links))
    print(f"🔎 Found {len(links)} Databricks articles")

    for idx, url in enumerate(links, start=1):
        try:
            driver.get(url)
            time.sleep(4)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            title_el = soup.find("h1")
            article = soup.find("article")

            if not title_el or not article:
                continue

            title = title_el.get_text(strip=True)
            md = markdownify.markdownify(str(article), heading_style="ATX")

            path = CARLY_DIR / f"{idx:03d}_{clean(title)}.md"
            path.write_text(f"# {title}\n\n**Source:** {url}\n\n{md}", encoding="utf-8")

            print(f"✓ Saved: {path.name}")
        except Exception as e:
            print(f"⚠️ Skipped: {url}")

    driver.quit()

# ================== MEDIUM ==================

def scrape_paul_levchuk():
    print("\n▶ Scraping Paul Levchuk (Medium – WORKING)")

    driver = get_driver()
    driver.get(PAUL_URL)
    time.sleep(5)

    # SCROLL to load posts
    for _ in range(6):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    links = []
    for a in driver.find_elements(By.XPATH, "//a[@href]"):
        href = a.get_attribute("href")
        if href and "/@paul.levchuk/" in href and "?" not in href:
            links.append(href)

    links = list(dict.fromkeys(links))
    print(f"🔎 Found {len(links)} Medium posts")

    for idx, url in enumerate(links, start=1):
        try:
            driver.get(url)
            time.sleep(4)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            title_el = soup.find("h1")
            article = soup.find("article")

            if not title_el or not article:
                continue

            title = title_el.get_text(strip=True)
            md = markdownify.markdownify(str(article), heading_style="ATX")

            path = PAUL_DIR / f"{idx:03d}_{clean(title)}.md"
            path.write_text(f"# {title}\n\n**Source:** {url}\n\n{md}", encoding="utf-8")

            print(f"✓ Saved: {path.name}")
        except Exception:
            print(f"⚠️ Skipped: {url}")

    driver.quit()

# ================== RUN ==================

if __name__ == "__main__":
    scrape_carly_taylor()
    scrape_paul_levchuk()
    print("\n🎉 DONE — BOTH DATABRICKS + MEDIUM FILES SAVED")
