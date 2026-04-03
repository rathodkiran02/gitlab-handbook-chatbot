import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types

load_dotenv()
ROOT = Path(__file__).parent.parent

# ── clients ────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(api_version='v1beta')
)

# ── embedding model ────────────────────────────────────────────────────────
print("🔄 Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model ready!")

# ── chromadb ───────────────────────────────────────────────────────────────
CHROMA_PATH = ROOT / "chroma_db"
chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
handbook_collection  = chroma_client.get_collection("handbook")
direction_collection = chroma_client.get_collection("direction")

# ── HyDE — Hypothetical Document Embedding ─────────────────────────────────
def generate_hypothetical_answer(question: str) -> str:
    """
    HyDE: Ask Gemini to generate a fake ideal answer.
    We embed THIS instead of the raw question.
    This bridges the gap between question style and document style.
    """
    prompt = f"""You are a GitLab expert. Write a short paragraph (3-4 sentences) 
that would be the ideal answer to this question, as if it came directly 
from the GitLab Handbook or Direction pages.

Question: {question}

Write only the answer paragraph, no preamble."""

    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=200
        )
    )
    return response.text.strip()

# ── BM25 keyword search ────────────────────────────────────────────────────
def bm25_search(query: str, collection, n_results: int = 5):
    """
    Simple keyword-based search using ChromaDB's where_document filter.
    Poor man's BM25 — searches for key terms in documents.
    """
    # extract key words (remove common words)
    stopwords = {'what','is','the','how','do','does','a','an','to','of','in',
                 'and','or','for','with','are','was','were','be','been','have'}
    words = [w.lower() for w in query.split() if w.lower() not in stopwords]
    
    if not words:
        return []

    results = []
    # search for each keyword and collect results
    for word in words[:3]:  # top 3 keywords only
        try:
            r = collection.query(
                query_texts=[word],
                n_results=min(n_results, collection.count()),
                include=["documents", "metadatas", "distances"]
            )
            if r['documents'][0]:
                for doc, meta, dist in zip(
                    r['documents'][0],
                    r['metadatas'][0],
                    r['distances'][0]
                ):
                    results.append({
                        "text": doc,
                        "source": meta.get("source", ""),
                        "url": meta.get("url", ""),
                        "score": 1 - dist,
                        "search_type": "keyword"
                    })
        except:
            pass
    return results

# ── vector semantic search ─────────────────────────────────────────────────
def vector_search(query_embedding, collection, n_results: int = 5):
    """Semantic vector search using embeddings."""
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        chunks = []
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            chunks.append({
                "text": doc,
                "source": meta.get("source", ""),
                "url": meta.get("url", ""),
                "score": 1 - dist,
                "search_type": "semantic"
            })
        return chunks
    except Exception as e:
        print(f"⚠️ Vector search error: {e}")
        return []

# ── hybrid search ──────────────────────────────────────────────────────────
def hybrid_search(question: str, hyde_answer: str, collection, 
                  collection_name: str, n_results: int = 5):
    """
    Combine semantic (HyDE) + keyword (BM25) search.
    Deduplicate and rank by combined score.
    """
    # embed the hypothetical answer (HyDE)
    hyde_embedding = embedding_model.encode(hyde_answer).tolist()

    # run both searches
    semantic_results = vector_search(hyde_embedding, collection, n_results)
    keyword_results  = bm25_search(question, collection, n_results)

    # merge and deduplicate by text
    seen   = set()
    merged = []
    for chunk in semantic_results + keyword_results:
        key = chunk["text"][:100]  # use first 100 chars as key
        if key not in seen:
            seen.add(key)
            chunk["collection"] = collection_name
            merged.append(chunk)

    # sort by score descending
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:n_results]

# ── main RAG function ──────────────────────────────────────────────────────
def ask(question: str, chat_history: list = []) -> dict:
    """
    Main RAG pipeline:
    1. HyDE — generate hypothetical answer
    2. Hybrid search handbook + direction
    3. Merge and rank results
    4. Generate final answer with Gemini
    5. Return answer + sources
    """
    print(f"\n🤔 Question: {question}")

    # step 1 — HyDE
    print("📝 Generating hypothetical answer (HyDE)...")
    hyde_answer = generate_hypothetical_answer(question)
    print(f"   HyDE: {hyde_answer[:80]}...")

    # step 2 — hybrid search both collections
    print("🔍 Searching handbook + direction...")
    handbook_chunks  = hybrid_search(
        question, hyde_answer, handbook_collection,  "handbook",  n_results=5
    )
    direction_chunks = hybrid_search(
        question, hyde_answer, direction_collection, "direction", n_results=3
    )

    # step 3 — merge all context
    all_chunks = handbook_chunks + direction_chunks
    if not all_chunks:
        return {
            "answer": "I couldn't find relevant information for your question.",
            "sources": [],
            "hyde_answer": hyde_answer
        }

    # step 4 — build context string for Gemini
    context_parts = []
    for i, chunk in enumerate(all_chunks):
        source_label = "📘 Handbook" if chunk["collection"] == "handbook" else "🗺️ Direction"
        context_parts.append(
            f"[Source {i+1} — {source_label}]\n{chunk['text']}\n"
        )
    context = "\n---\n".join(context_parts)

    # step 5 — build chat history string
    history_str = ""
    if chat_history:
        history_str = "\n".join([
            f"User: {h['user']}\nAssistant: {h['assistant']}"
            for h in chat_history[-3:]  # last 3 turns only
        ])

    # step 6 — final prompt
    prompt = f"""You are a helpful GitLab assistant that helps employees and 
aspiring employees understand GitLab's handbook and product direction.

Use ONLY the context below to answer the question. 
If the context doesn't contain enough information, say so honestly.
Always mention whether information comes from the Handbook or Direction pages.
Be concise, clear and helpful.

{f'Previous conversation:{chr(10)}{history_str}{chr(10)}' if history_str else ''}

Context:
{context}

Question: {question}

Answer:"""

    print("💬 Generating answer with Gemini...")
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=1000
        )
    )

    answer = response.text.strip()

    # step 7 — build sources list
    sources = []
    seen_sources = set()
    for chunk in all_chunks:
        src = chunk["source"]
        if src not in seen_sources:
            seen_sources.add(src)
            sources.append({
                "source": src,
                "url": chunk["url"],
                "collection": chunk["collection"],
                "score": round(chunk["score"], 3)
            })

    print(f"✅ Answer ready! ({len(sources)} sources)")
    return {
        "answer": answer,
        "sources": sources,
        "hyde_answer": hyde_answer
    }

# ── quick test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = ask("What are GitLab's core values?")
    print("\n" + "=" * 60)
    print("ANSWER:")
    print(result["answer"])
    print("\nSOURCES:")
    for s in result["sources"]:
        print(f"  - [{s['collection']}] {s['source']}")