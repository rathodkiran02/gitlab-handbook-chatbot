from pathlib import Path
from tqdm import tqdm

ROOT         = Path(__file__).parent.parent
HANDBOOK_DIR = ROOT / "data" / "handbook" / "content" / "handbook"

# Direction-related folders inside the handbook
DIRECTION_FOLDERS = [
    "product/",
    "company/strategy",
    "company/vision",
    "engineering/development/",
    "product-development/",
    "marketing/brand-and-product-marketing/product-and-solution-marketing/",
]

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start  = 0
    while start < len(text):
        end   = start + chunk_size
        chunk = text[start:end]
        if len(chunk.strip()) > 50:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def scrape_all():
    print("📂 Loading direction content from handbook repo...")
    all_chunks = []

    # keywords that indicate strategy/direction content
    STRATEGY_KEYWORDS = [
        'strategy', 'direction', 'vision', 'roadmap', 'three year',
        '3 year', 'fy26', 'fy25', 'investment theme', 'product direction',
        'mission', 'objective', 'goal', 'plan', 'future'
    ]

    md_files = list(HANDBOOK_DIR.rglob("*.md"))
    print(f"📄 Scanning {len(md_files)} files for strategy content...")

    found = 0
    for filepath in tqdm(md_files, desc="Scanning"):
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
            text_lower = text.lower()

            # only include files with strategy/direction content
            keyword_count = sum(1 for kw in STRATEGY_KEYWORDS if kw in text_lower)
            if keyword_count < 2:
                continue

            rel_path = filepath.relative_to(ROOT / "data" / "handbook")
            source   = str(rel_path).replace("\\", "/")
            url      = f"https://handbook.gitlab.com/{source}".replace(".md", "")

            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text":     chunk,
                    "source":   source,
                    "url":      url,
                    "title":    filepath.stem,
                    "chunk_id": f"direction_{source}_{i}"
                })
            found += 1
        except:
            pass

    print(f"\n✅ Found {found} strategy-related files → {len(all_chunks)} chunks")
    return all_chunks

if __name__ == "__main__":
    chunks = scrape_all()
    print(f"\n🎉 Direction pipeline ready! {len(chunks)} chunks")