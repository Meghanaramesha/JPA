import os
import re

ROOT = "GitBook_Content"

def clean_title(text):
    """Remove characters that break YAML."""
    return re.sub(r'[^a-zA-Z0-9 \-\_\.\(\)]', '', text)

def fix_markdown_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract first heading as title
    heading_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    if heading_match:
        raw_title = heading_match.group(1).strip()
    else:
        raw_title = os.path.splitext(os.path.basename(path))[0]

    title = clean_title(raw_title)

    # Remove existing YAML block if present
    content = re.sub(r'^---[\s\S]*?---', '', content, count=1).strip()

    # Build new safe YAML header
    yaml_header = f"---\ntitle: \"{title}\"\n---\n\n"

    new_content = yaml_header + content

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✔ Fixed YAML: {path}")

def scan_and_fix():
    for root, dirs, files in os.walk(ROOT):
        for file in files:
            if file.lower().endswith(".md"):
                fix_markdown_file(os.path.join(root, file))

    print("\n🎉 DONE! All YAML cleaned and GitBook-safe.")

if __name__ == "__main__":
    scan_and_fix()
