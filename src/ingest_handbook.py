import os
import sys
from pathlib import Path
from tqdm import tqdm

# ── paths ──────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
HANDBOOK_DIR = ROOT / "data" / "handbook"
CLONE_URL   = "https://gitlab.com/gitlab-com/content-sites/handbook.git"

def clone_handbook():
    """Clone the GitLab handbook repo if not already cloned."""
    if (HANDBOOK_DIR / ".git").exists():
        print("✅ Handbook already cloned. Skipping.")
        return

    print("📥 Cloning GitLab Handbook (this may take 2-5 mins)...")
    import subprocess
    result = subprocess.run(
        ["git", "clone", "--depth=1", CLONE_URL, str(HANDBOOK_DIR)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ Clone failed:", result.stderr)
        sys.exit(1)
    print("✅ Handbook cloned successfully!")

def load_markdown_files():
    """Walk handbook directory and load all .md files."""
    md_dir = HANDBOOK_DIR / "content" / "handbook"
    
    if not md_dir.exists():
        # fallback: search entire handbook dir
        md_dir = HANDBOOK_DIR

    print(f"📂 Reading markdown files from: {md_dir}")
    
    docs = []
    md_files = list(md_dir.rglob("*.md"))
    print(f"📄 Found {len(md_files)} markdown files")

    for filepath in tqdm(md_files, desc="Loading files"):
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
            # skip empty or very short files
            if len(text.strip()) < 100:
                continue
            # get relative path for metadata
            rel_path = filepath.relative_to(HANDBOOK_DIR)
            docs.append({
                "text": text,
                "source": str(rel_path),
                "url": f"https://handbook.gitlab.com/{rel_path}".replace("\\", "/").replace(".md", "")
            })
        except Exception as e:
            print(f"⚠️  Could not read {filepath}: {e}")

    print(f"✅ Loaded {len(docs)} documents")
    return docs

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if len(chunk.strip()) > 50:  # skip tiny chunks
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def chunk_documents(docs):
    """Chunk all documents."""
    print("✂️  Chunking documents...")
    all_chunks = []
    for doc in tqdm(docs, desc="Chunking"):
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["source"],
                "url": doc["url"],
                "chunk_id": f"{doc['source']}_{i}"
            })
    print(f"✅ Created {len(all_chunks)} chunks")
    return all_chunks

if __name__ == "__main__":
    clone_handbook()
    docs   = load_markdown_files()
    chunks = chunk_documents(docs)
    
    # save chunk count for next step
    print(f"\n🎉 Handbook pipeline ready! {len(chunks)} chunks to embed.")
    print("👉 Run ingest_direction.py next")