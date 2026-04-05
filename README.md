# 🦊 GitLab Handbook Assistant

An AI-powered chatbot that helps employees and aspiring employees easily access information from GitLab's Handbook and Direction pages — built with **Hybrid RAG + HyDE retrieval**.

## 🌐 Live Demo
🔗 [https://gl-assistant-bot.streamlit.app/](https://gl-assistant-bot.streamlit.app/)

## 👤 Author
**R Kiran Kumar**
GitHub: [https://github.com/rathodkiran02](https://github.com/rathodkiran02)

---

## 🧠 How It Works

This chatbot utilizes an **Advanced Hybrid RAG** (Retrieval-Augmented Generation) pipeline to ensure high accuracy and context-aware responses:

1.  **Query Expansion**: Automatically enriches the user's question with GitLab-specific terminology.
2.  **HyDE (Hypothetical Document Embeddings)**: Gemini generates a "hypothetical" ideal answer to bridge the gap between user questions and technical documentation.
3.  **Hybrid Search**: Combines semantic vector search (via ChromaDB) with keyword matching across **75,000+ chunks**.
4.  **Dual Collection Retrieval**: Searches the Handbook and Direction pages separately to ensure strategic and operational data are both considered.
5.  **Grounded Generation**: Gemini 2.0 Flash synthesizes the final answer, strictly using the retrieved context with source citations.

---

## ✨ Features

- 💬 **Natural Conversation**: Supports multi-turn dialogue and remembers context.
- 📚 **Massive Knowledge Base**: Indexed GitLab's entire public handbook and direction site.
- 🔍 **Hybrid RAG & HyDE**: Advanced retrieval techniques to minimize hallucinations.
- 📖 **Source Citations**: Every answer includes links/references to the original GitLab pages.
- 🎨 **UI Customization**: Includes Light, Dark, and Blue themes via Streamlit.
- 🛡️ **Smart Guardrails**: Gracefully handles off-topic queries and provides "GitLab Facts" during loading.
- ⚡ **Model Fallback**: Automated switching between Gemini models to manage API quotas.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | Streamlit |
| **LLM** | Google Gemini 2.0 Flash |
| **Embeddings** | `sentence-transformers` (all-MiniLM-L6-v2) |
| **Vector Store** | ChromaDB |
| **Data Ingestion** | Git (Handbook) & BeautifulSoup (Direction Scraping) |

---

## 🗂️ Project Structure

```text
gitlab-handbook-chatbot/
├── app.py                        # Main Streamlit UI
├── src/
│   ├── rag_engine.py             # RAG pipeline (HyDE + Hybrid search)
│   ├── ingest_handbook.py        # Clone + smart chunk GitLab handbook
│   ├── ingest_direction.py       # Scrape + chunk direction pages
│   ├── build_vectorstore.py      # Build ChromaDB vector store
│   ├── clear_db.py               # Database maintenance
│   └── debug_search.py           # Retrieval quality testing
├── data/                         # Local storage for cloned/scraped content
├── chroma_db/                    # Persistent vector storage
├── requirements.txt              # Dependencies
└── .env                          # API keys
🚀 Setup & Run Locally

Prerequisites

Python 3.10+

Gemini API key from AI Studio

1. Clone & Install
Bash
git clone [https://github.com/rathodkiran02/gitlab-handbook-chatbot](https://github.com/rathodkiran02/gitlab-handbook-chatbot)
cd gitlab-handbook-chatbot
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows

pip install -r requirements.txt

2. Environment Setup

Create a .env file in the root directory:

Code snippet

GEMINI_API_KEY=your_gemini_api_key_here

3. Build Data Pipeline

Run the ingestion script (Note: First run takes ~20 mins due to the size of the GitLab Handbook).

Bash
python src/build_vectorstore.py

4. Launch App

Bash
streamlit run app.py

🎯 Example Questions
"What are GitLab's core CREDIT values?"

"How does GitLab handle 'unlimited' PTO?"

"How do I prepare for a technical interview at GitLab?"
