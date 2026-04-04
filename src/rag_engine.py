import os
import sys
import time
import hashlib
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types

load_dotenv()
ROOT = Path(__file__).parent.parent

# ── simple cache ───────────────────────────────────────────────────────────
_cache = {}

def _cache_key(question: str) -> str:
    return hashlib.md5(question.lower().strip().encode()).hexdigest()

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

# ── model list with fallbacks ──────────────────────────────────────────────
MODELS = [
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.5-flash',
]

def generate_with_fallback(prompt: str, temperature: float = 0.0,
                           max_tokens: int = 1000) -> str:
    """Try models in order, fall back if quota exhausted."""
    for model_name in MODELS:
        for attempt in range(2):
            try:
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                return response.text.strip()
            except Exception as e:
                err = str(e)
                if '429' in err:
                    print(f"⚠️ {model_name} quota exhausted, trying next...")
                    time.sleep(2)
                    break
                elif '503' in err or '500' in err:
                    if attempt == 0:
                        print(f"⚠️ {model_name} unavailable, retrying in 5s...")
                        time.sleep(5)
                    else:
                        print(f"⚠️ {model_name} still unavailable, trying next...")
                        break
                else:
                    if attempt == 0:
                        print(f"⚠️ Error ({model_name}): {e}, retrying...")
                        time.sleep(3)
                    else:
                        raise e
    raise Exception("All Gemini models exhausted. Please try again later.")

# ── query expansion (no API calls) ────────────────────────────────────────
EXPANSIONS = {
    'remote work':    'all-remote',
    'work from home': 'all-remote',
    'wfh':            'all-remote',
    'vacation':       'PTO paid time off',
    'time off':       'PTO paid time off',
    'salary':         'compensation',
    'pay':            'compensation',
    'interview':      'hiring process',
    '3 year':         'three year strategy',
    'three year':     'strategy direction',
    'mental health':  'wellbeing mental health',
    'sick':           'sick leave PTO',
    'benefits':       'compensation benefits',
}

def rewrite_query(question: str) -> str:
    """Expand query with GitLab-specific terms — no API call."""
    q = question.lower()
    for term, expansion in EXPANSIONS.items():
        if term in q:
            return question + " " + expansion
    return question

# ── HyDE ───────────────────────────────────────────────────────────────────
def generate_hypothetical_answer(question: str) -> str:
    """
    HyDE: Generate a hypothetical ideal answer to improve retrieval.
    We embed this instead of the raw question.
    """
    prompt = f"""You are a GitLab expert. Write a short paragraph (3-4 sentences) 
that would be the ideal answer to this question, as if it came directly 
from the GitLab Handbook or Direction pages.

Question: {question}

Write only the answer paragraph, no preamble."""

    return generate_with_fallback(prompt, temperature=0.1, max_tokens=200)

# ── BM25 keyword search ────────────────────────────────────────────────────
def bm25_search(query: str, collection, n_results: int = 5):
    """Keyword-based search — catches exact term matches."""
    stopwords = {
        'what','is','the','how','do','does','a','an','to','of','in',
        'and','or','for','with','are','was','were','be','been','have',
        'i','me','my','we','our','you','your','it','its','this','that'
    }
    words = [w.lower() for w in query.split() if w.lower() not in stopwords]
    if not words:
        return []

    results = []
    for word in words[:3]:
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
                        "text":        doc,
                        "source":      meta.get("source", ""),
                        "url":         meta.get("url", ""),
                        "score":       1 - dist,
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
                "text":        doc,
                "source":      meta.get("source", ""),
                "url":         meta.get("url", ""),
                "score":       1 - dist,
                "search_type": "semantic"
            })
        return chunks
    except Exception as e:
        print(f"⚠️ Vector search error: {e}")
        return []

# ── hybrid search ──────────────────────────────────────────────────────────
def hybrid_search(question: str, hyde_answer: str, collection,
                  collection_name: str, n_results: int = 5):
    """Combine semantic (HyDE) + keyword search, deduplicate and rank."""
    hyde_embedding   = embedding_model.encode(hyde_answer).tolist()
    semantic_results = vector_search(hyde_embedding, collection, n_results)
    keyword_results  = bm25_search(question, collection, n_results)

    seen   = set()
    merged = []
    for chunk in semantic_results + keyword_results:
        key = chunk["text"][:100]
        if key not in seen:
            seen.add(key)
            chunk["collection"] = collection_name
            merged.append(chunk)

    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:n_results]

# ── guardrail ──────────────────────────────────────────────────────────────
IRRELEVANT_TOPICS = [
    'recipe', 'cook', 'food', 'sport', 'football', 'cricket', 'movie',
    'film', 'music', 'song', 'weather', 'stock', 'crypto', 'bitcoin',
    'relationship', 'dating', 'love', 'game', 'minecraft', 'fortnite'
]

VAGUE_QUESTIONS = [
    'tell me everything', 'everything', 'tell me all',
    'what do you know', 'explain everything', 'all information'
]

def is_irrelevant(question: str) -> bool:
    q = question.lower().strip()
    if any(vague in q for vague in VAGUE_QUESTIONS):
        return True
    return any(topic in q for topic in IRRELEVANT_TOPICS)

# ── main RAG function ──────────────────────────────────────────────────────
def ask(question: str, chat_history: list = []) -> dict:
    """
    Main RAG pipeline:
    1. Guardrail check
    2. Cache check
    3. Query expansion — GitLab-specific terms
    4. HyDE — generate hypothetical answer
    5. Hybrid search handbook + direction
    6. Generate final answer with Gemini
    7. Return answer + sources
    """
    print(f"\n🤔 Question: {question}")

    # guardrail
    if is_irrelevant(question):
        return {
            "answer": "👋 I'm specifically designed to answer questions about GitLab's handbook, culture, processes, and product direction. I'm not able to help with that topic. Try asking me about GitLab's values, hiring process, remote work policy, or product strategy!",
            "sources": [],
            "hyde_answer": ""
        }

    # cache check
    ck = _cache_key(question)
    if ck in _cache:
        print("⚡ Cache hit!")
        return _cache[ck]

    # step 1 — expand query
    print("🔄 Expanding query...")
    rewritten = rewrite_query(question)
    print(f"   Expanded: {rewritten}")

    # step 2 — HyDE
    print("📝 Generating hypothetical answer (HyDE)...")
    hyde_answer = generate_hypothetical_answer(rewritten)
    print(f"   HyDE: {hyde_answer[:80]}...")

    # step 3 — hybrid search both collections
    print("🔍 Searching handbook + direction...")
    handbook_chunks  = hybrid_search(
        rewritten, hyde_answer, handbook_collection,  "handbook",  n_results=12
    )
    direction_chunks = hybrid_search(
        rewritten, hyde_answer, direction_collection, "direction", n_results=4
    )

    # step 4 — merge all context
    all_chunks = handbook_chunks + direction_chunks
    if not all_chunks:
        return {
            "answer": "I couldn't find relevant information for your question. Try rephrasing or ask about a specific GitLab topic.",
            "sources": [],
            "hyde_answer": hyde_answer
        }

    # step 5 — build context string
    context_parts = []
    for i, chunk in enumerate(all_chunks):
        source_label = "📘 Handbook" if chunk["collection"] == "handbook" else "🗺️ Direction"
        context_parts.append(f"[Source {i+1} — {source_label}]\n{chunk['text']}\n")
    context = "\n---\n".join(context_parts)

    # step 6 — chat history
    history_str = ""
    if chat_history:
        history_str = "\n".join([
            f"User: {h['user']}\nAssistant: {h['assistant']}"
            for h in chat_history[-3:]
        ])

    # step 7 — final prompt
    prompt = f"""You are an expert GitLab assistant helping employees and aspiring 
employees navigate GitLab's handbook and product direction.

INSTRUCTIONS:
- Answer thoroughly using the context provided below
- Extract actual text from markdown links like [text](/url) — use the text, ignore URLs
- Synthesize information from ALL sources provided, don't just look at one
- Structure answers clearly with bullet points when listing multiple items
- Always mention whether info comes from Handbook or Direction pages
- If question is completely unrelated to GitLab, politely decline and redirect
- Never invent information not present in context
- If context has partial info, give best answer and note what may be missing
- Use markdown tables when comparing multiple items side by side
- Use bullet points for lists of 3+ items
- Use headers (##) for multi-part answers

TONE: Professional, friendly — like a knowledgeable GitLab teammate

{f'Previous conversation:{chr(10)}{history_str}{chr(10)}' if history_str else ''}

Context:
{context}

Question: {question}

Answer:"""

    print("💬 Generating answer with Gemini...")
    answer = generate_with_fallback(prompt, temperature=0.0, max_tokens=1000)

    # step 8 — build sources
    sources   = []
    seen_srcs = set()
    for chunk in all_chunks:
        src = chunk["source"]
        if src not in seen_srcs:
            seen_srcs.add(src)
            sources.append({
                "source":     src,
                "url":        chunk["url"],
                "collection": chunk["collection"],
                "score":      round(chunk["score"], 3)
            })

    print(f"✅ Answer ready! ({len(sources)} sources)")

    result = {
        "answer":      answer,
        "sources":     sources,
        "hyde_answer": hyde_answer
    }
    _cache[ck] = result
    return result

# ── quick test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = ask("What are GitLab's core values?")
    print("\n" + "=" * 60)
    print("ANSWER:")
    print(result["answer"])
    print("\nSOURCES:")
    for s in result["sources"]:
        print(f"  - [{s['collection']}] {s['source']}")