import requests
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import time

# ── paths ──────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
DIRECTION_DIR = ROOT / "data" / "direction"
DIRECTION_DIR.mkdir(parents=True, exist_ok=True)

# ── all direction pages to scrape ──────────────────────────────────────────
DIRECTION_URLS = [
    "https://about.gitlab.com/direction/",
    "https://about.gitlab.com/direction/dev/",
    "https://about.gitlab.com/direction/ops/",
    "https://about.gitlab.com/direction/security/",
    "https://about.gitlab.com/direction/growth/",
    "https://about.gitlab.com/direction/data-science/",
    "https://about.gitlab.com/direction/create/",
    "https://about.gitlab.com/direction/plan/",
    "https://about.gitlab.com/direction/verify/",
    "https://about.gitlab.com/direction/deploy/",
    "https://about.gitlab.com/direction/monitor/",
    "https://about.gitlab.com/direction/manage/",
    "https://about.gitlab.com/direction/configure/",
    "https://about.gitlab.com/direction/govern/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GitLabChatbot/1.0)"
}

def scrape_page(url):
    """Scrape a single direction page and return clean text."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"⚠️  Skipping {url} (status {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # remove navbars, footers, scripts, styles
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()

        # get page title
        title = soup.find("h1")
        title_text = title.get_text(strip=True) if title else "GitLab Direction"

        # extract all meaningful text
        content_tags = soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td"])
        lines = []
        for tag in content_tags:
            text = tag.get_text(strip=True)
            if len(text) > 30:  # skip very short lines
                lines.append(text)

        full_text = "\n\n".join(lines)
        return {
            "title": title_text,
            "text": full_text,
            "url": url,
            "source": f"direction/{url.split('/direction/')[-1].strip('/') or 'index'}"
        }

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if len(chunk.strip()) > 50:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def scrape_all():
    """Scrape all direction pages and chunk them."""
    print(f"🌐 Scraping {len(DIRECTION_URLS)} Direction pages...\n")
    
    all_chunks = []
    
    for url in tqdm(DIRECTION_URLS, desc="Scraping pages"):
        doc = scrape_page(url)
        if doc is None:
            continue
            
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["source"],
                "url": doc["url"],
                "title": doc["title"],
                "chunk_id": f"direction_{doc['source']}_{i}"
            })
        
        print(f"  ✅ {doc['title']} → {len(chunks)} chunks")
        time.sleep(1)  # be polite, don't hammer the server

    print(f"\n✅ Direction scraping complete! {len(all_chunks)} total chunks")
    return all_chunks

if __name__ == "__main__":
    chunks = scrape_all()
    print(f"\n🎉 Direction pipeline ready! {len(chunks)} chunks")
    print("👉 Run build_vectorstore.py next")