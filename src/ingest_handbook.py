import os
import sys
import re
from pathlib import Path
from tqdm import tqdm

ROOT         = Path(__file__).parent.parent
HANDBOOK_DIR = ROOT / "data" / "handbook"
CLONE_URL    = "https://gitlab.com/gitlab-com/content-sites/handbook.git"

def clone_handbook():
    if (HANDBOOK_DIR / ".git").exists():
        print("✅ Handbook already cloned. Skipping.")
        return
    print("📥 Cloning GitLab Handbook...")
    import subprocess
    result = subprocess.run(
        ["git", "clone", "--depth=1", CLONE_URL, str(HANDBOOK_DIR)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ Clone failed:", result.stderr)
        sys.exit(1)
    print("✅ Handbook cloned!")

def extract_frontmatter(text):
    """Separate YAML frontmatter from markdown body."""
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()
    return None, text

def chunk_by_sections(text, source, url, max_chunk_size=1000, overlap=100):
    """
    Smart chunking strategy:
    1. Keep YAML frontmatter as one chunk
    2. Split by markdown headings (##, ###)
    3. If section too long, split by paragraphs
    4. Never cut mid-sentence
    """
    chunks = []
    frontmatter, body = extract_frontmatter(text)

    # chunk 1 — frontmatter as its own chunk (structured data stays intact)
    if frontmatter and len(frontmatter.strip()) > 50:
        chunks.append({
            "text":     f"[Metadata]\n{frontmatter}",
            "source":   source,
            "url":      url,
            "chunk_id": f"{source}_frontmatter"
        })

    # split body by headings
    # regex: split on lines starting with # ## ### etc
    heading_pattern = re.compile(r'\n(?=#{1,4} )')
    sections = heading_pattern.split(body)

    for sec_idx, section in enumerate(sections):
        section = section.strip()
        if not section or len(section) < 50:
            continue

        # if section fits in one chunk — keep it whole
        if len(section) <= max_chunk_size:
            chunks.append({
                "text":     section,
                "source":   source,
                "url":      url,
                "chunk_id": f"{source}_sec{sec_idx}"
            })
        else:
            # section too big — split by paragraphs
            paragraphs = [p.strip() for p in section.split('\n\n') if p.strip()]
            current_chunk = ""
            para_idx = 0

            for para in paragraphs:
                if len(current_chunk) + len(para) <= max_chunk_size:
                    current_chunk += "\n\n" + para
                else:
                    # save current chunk
                    if len(current_chunk.strip()) > 50:
                        chunks.append({
                            "text":     current_chunk.strip(),
                            "source":   source,
                            "url":      url,
                            "chunk_id": f"{source}_sec{sec_idx}_p{para_idx}"
                        })
                        para_idx += 1
                    # start new chunk with overlap
                    # keep last sentence of previous chunk for context
                    sentences = current_chunk.split('. ')
                    overlap_text = '. '.join(sentences[-2:]) if len(sentences) > 1 else ""
                    current_chunk = overlap_text + "\n\n" + para

            # save last chunk
            if len(current_chunk.strip()) > 50:
                chunks.append({
                    "text":     current_chunk.strip(),
                    "source":   source,
                    "url":      url,
                    "chunk_id": f"{source}_sec{sec_idx}_p{para_idx}_last"
                })

    return chunks

def load_markdown_files():
    md_dir = HANDBOOK_DIR / "content" / "handbook"
    if not md_dir.exists():
        md_dir = HANDBOOK_DIR

    print(f"📂 Reading markdown files from: {md_dir}")
    docs = []
    md_files = list(md_dir.rglob("*.md"))
    print(f"📄 Found {len(md_files)} markdown files")

    for filepath in tqdm(md_files, desc="Loading files"):
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
            if len(text.strip()) < 100:
                continue
            rel_path = filepath.relative_to(HANDBOOK_DIR)
            docs.append({
                "text":   text,
                "source": str(rel_path),
                "url":    f"https://handbook.gitlab.com/{rel_path}".replace("\\", "/").replace(".md", "")
            })
        except Exception as e:
            print(f"⚠️  Could not read {filepath}: {e}")

    print(f"✅ Loaded {len(docs)} documents")
    return docs

def chunk_documents(docs):
    """Smart chunk all documents."""
    print("✂️  Smart chunking documents...")
    all_chunks = []
    for doc in tqdm(docs, desc="Chunking"):
        chunks = chunk_by_sections(
            doc["text"],
            doc["source"],
            doc["url"]
        )
        all_chunks.extend(chunks)
    print(f"✅ Created {len(all_chunks)} smart chunks")
    return all_chunks

if __name__ == "__main__":
    clone_handbook()
    docs   = load_markdown_files()
    chunks = chunk_documents(docs)
    print(f"\n🎉 Smart chunking done! {len(chunks)} chunks")