import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).parent.parent
chroma_client = chromadb.PersistentClient(path=str(ROOT / "chroma_db"))
handbook_collection = chroma_client.get_collection("handbook")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

query = "GitLab core values CREDIT collaboration results efficiency diversity iteration transparency"
embedding = embedding_model.encode(query).tolist()

results = handbook_collection.query(
    query_embeddings=[embedding],
    n_results=5,
    include=["documents", "metadatas", "distances"]
)

print("TOP 5 RESULTS:\n")
for i, (doc, meta, dist) in enumerate(zip(
    results['documents'][0],
    results['metadatas'][0],
    results['distances'][0]
)):
    print(f"Result {i+1} | score: {1-dist:.3f} | source: {meta['source']}")
    print(f"Preview: {doc[:300]}")
    print("-" * 60)