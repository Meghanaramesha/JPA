import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ================= CONFIG =================

BASE_DIR = (
    "GitBook_Content/Influencers/"
    "Publishing_PR_Influencer_Agencies/"
    "Harry_Phokou/YouTube"
)
os.makedirs(BASE_DIR, exist_ok=True)

CHANNEL_URL = "https://www.youtube.com/@hphokou/videos"

# ================= DRIVER =================

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# ================= HELPERS =================

def clean_filename(text: str) -> str:
    return "".join(c for c in text if c.isalnum() or c in " -_()").strip()[:120]

# ================= SCRAPER =================

def extract_videos_with_descriptions():
    print("▶ Extracting YouTube videos (single-page format)...")

    driver = get_driver()
    driver.get(CHANNEL_URL)
    time.sleep(10)

    video_links = []
    seen = set()

    # Collect video URLs (order preserved)
    for a in driver.find_elements(By.XPATH, "//a[@href]"):
        href = a.get_attribute("href")
        if href and "/watch?v=" in href:
            vid = href.split("v=")[1].split("&")[0]
            if vid not in seen:
                seen.add(vid)
                video_links.append(f"https://www.youtube.com/watch?v={vid}")

    print(f"🔎 Found {len(video_links)} videos")

    # Visit each video → ONE markdown file
    for idx, url in enumerate(video_links, start=1):
        try:
            driver.get(url)
            time.sleep(6)

            title = driver.title.replace(" - YouTube", "").strip()

            # FULL description as ONE block
            description = driver.execute_script("""
                try {
                    return ytInitialPlayerResponse.videoDetails.shortDescription;
                } catch (e) {
                    return "";
                }
            """)

            filename = f"{idx:03d}_{clean_filename(title)}.md"
            path = os.path.join(BASE_DIR, filename)

            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    f"# {title}\n\n"
                    f"**YouTube URL:** {url}\n\n"
                    f"{description if description else '_No description available._'}\n"
                )

            print(f"✅ Saved: {filename}")

        except Exception:
            print(f"⚠️ Skipped: {url}")

    driver.quit()
    print("\n🎯 Harry Phokou YouTube extraction completed successfully")

# ================= RUN =================

if __name__ == "__main__":
    extract_videos_with_descriptions()
