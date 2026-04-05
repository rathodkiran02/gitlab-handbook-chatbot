import os
import sys
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()
ROOT = Path(__file__).parent.parent

# ── local embedding model (free, no API limits) ────────────────────────────
print("🔄 Loading embedding model (first time downloads ~90MB)...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model loaded!")

# ── chromadb setup ─────────────────────────────────────────────────────────
CHROMA_PATH = ROOT / "chroma_db"
chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

handbook_collection = chroma_client.get_or_create_collection(
    name="handbook", metadata={"hnsw:space": "cosine"}
)
direction_collection = chroma_client.get_or_create_collection(
    name="direction", metadata={"hnsw:space": "cosine"}
)

def get_embedding(text):
    return embedding_model.encode(text).tolist()

def load_handbook_chunks():
    sys.path.insert(0, str(ROOT / "src"))
    from ingest_handbook import load_markdown_files, chunk_documents
    docs = load_markdown_files()
    return chunk_documents(docs)

def load_direction_chunks():
    from ingest_direction import scrape_all
    return scrape_all()

def embed_and_store(chunks, collection, label, batch_size=100):
    print(f"\n📦 Embedding {len(chunks)} {label} chunks...")

    try:
        count = collection.count()
        if count > 0:
            print(f"   ✅ Already have {count} chunks, skipping!")
            return
    except:
        pass
    print(f"   ⏭️  {len(chunks)} new chunks to embed")

    if not chunks:
        print(f"   ✅ All {label} chunks already embedded!")
        return

    for i in tqdm(range(0, len(chunks), batch_size), desc=f"Embedding {label}"):
        batch     = chunks[i: i + batch_size]
        ids       = [c["chunk_id"] for c in batch]
        texts     = [c["text"]     for c in batch]
        metadatas = [{"source": c["source"], "url": c.get("url", "")} for c in batch]

        # batch embed — much faster than one by one
        embeddings = embedding_model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    print(f"✅ {label} done!")

if __name__ == "__main__":
    print("=" * 60)
    print("  GitLab Chatbot — Vector Store Builder")
    print("=" * 60)

    print("\n📍 Step 1: Direction pages")
    direction_chunks = load_direction_chunks()
    embed_and_store(direction_chunks, direction_collection, "direction")

    print("\n📍 Step 2: Handbook (~10-15 mins locally ☕)")
    handbook_chunks = load_handbook_chunks()
    embed_and_store(handbook_chunks, handbook_collection, "handbook")

    print("\n" + "=" * 60)
    print("🎉 Done! Vector store ready.")
    print("=" * 60)