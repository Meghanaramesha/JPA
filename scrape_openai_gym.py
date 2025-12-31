import os
import shutil
import subprocess
from pathlib import Path

# ================= CONFIG =================

REPO_URL = "https://github.com/Farama-Foundation/Gymnasium.git"
REPO_DIR = Path("Gymnasium_repo")

OUTPUT_DIR = Path("GitBook_Content") / "OpenAI_Gym"

DOCS_SRC = REPO_DIR / "docs"

# ================= HELPERS =================

def run(cmd):
    subprocess.run(cmd, check=True, shell=True)

def clone_repo():
    if REPO_DIR.exists():
        print("📦 Repo already exists, skipping clone")
        return
    print("📥 Cloning Gymnasium repo...")
    run(f"git clone {REPO_URL} {REPO_DIR}")

def ensure_output():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def copy_docs():
    if not DOCS_SRC.exists():
        raise RuntimeError("❌ docs/ folder not found in repo")

    print("📂 Copying documentation files...")

    for item in DOCS_SRC.iterdir():
        target = OUTPUT_DIR / item.name

        # Skip build/config files not needed for GitBook
        if item.name.startswith("_") or item.suffix in [".yml", ".yaml"]:
            continue

        if item.is_dir():
            if not target.exists():
                shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

def main():
    print("🚀 Building OpenAI Gym documentation from GitHub source")
    clone_repo()
    ensure_output()
    copy_docs()
    print("✅ DONE — Docs extracted in original order")
    print("➡️ You can now convert .rst → .md if needed")

if __name__ == "__main__":
    main()
