# 🤖 GitLab Handbook Assistant

An AI-powered chatbot that helps employees and aspiring candidates easily access insights from GitLab’s **Handbook** and **Direction pages** using an advanced **Hybrid RAG + HyDE pipeline**.

---

## 🌐 Live Demo

🔗 https://gl-assistant-bot.streamlit.app/

---

## 👤 Author

**R Kiran Kumar**
GitHub: https://github.com/rathodkiran02

---

## 🧠 How It Works

This project implements an **Advanced Retrieval-Augmented Generation (RAG)** system designed for high accuracy and minimal hallucination.

### 🔍 Core Pipeline

* **Query Expansion**
  Enhances user queries with GitLab-specific terminology.

* **HyDE (Hypothetical Document Embeddings)**
  Generates a hypothetical ideal answer using Gemini to improve retrieval relevance.

* **Hybrid Search**
  Combines:

  * Semantic Search (ChromaDB)
  * Keyword Matching

* **Dual Collection Retrieval**
  Retrieves from:

  * GitLab Handbook (operational data)
  * GitLab Direction pages (strategic data)

* **Grounded Generation**
  Final response is generated using **Gemini 2.0 Flash**, strictly based on retrieved context with citations.

---

## ✨ Features

* 💬 **Conversational AI** – Supports multi-turn conversations with memory
* 📚 **Massive Knowledge Base** – 75,000+ indexed document chunks
* 🔍 **Hybrid RAG + HyDE** – Reduces hallucinations significantly
* 📖 **Source Citations** – Every response is grounded with references
* 🎨 **Custom UI Themes** – Light, Dark, Blue (Streamlit)
* 🛡️ **Smart Guardrails** – Handles irrelevant queries gracefully
* ⚡ **Model Fallback System** – Automatically switches Gemini models when quota limits are reached

---

## 🛠️ Tech Stack

| Component      | Technology                                |
| -------------- | ----------------------------------------- |
| Frontend       | Streamlit                                 |
| LLM            | Gemini 2.0 Flash                          |
| Embeddings     | sentence-transformers (all-MiniLM-L6-v2)  |
| Vector Store   | ChromaDB                                  |
| Data Ingestion | Git (Handbook) + BeautifulSoup (Scraping) |

---

## 🗂️ Project Structure

```bash
gitlab-handbook-chatbot/
├── app.py                        # Streamlit UI
├── src/
│   ├── rag_engine.py             # Core RAG pipeline
│   ├── ingest_handbook.py        # Handbook ingestion
│   ├── ingest_direction.py       # Direction pages scraping
│   ├── build_vectorstore.py      # Build vector DB
│   ├── clear_db.py               # Reset database
│   └── debug_search.py           # Debug retrieval
├── data/                         # Raw data storage
├── chroma_db/                    # Vector database
├── requirements.txt
└── .env
```

---

## 🚀 Setup & Run Locally

### ✅ Prerequisites

* Python 3.10+
* Gemini API key (Google AI Studio)

---

### 1️⃣ Clone Repository

```bash
git clone https://github.com/rathodkiran02/gitlab-handbook-chatbot
cd gitlab-handbook-chatbot
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Environment Setup

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

### 5️⃣ Build Vector Database

```bash
python src/build_vectorstore.py
```

⚠️ First run may take ~20 minutes due to large dataset ingestion.

---

### 6️⃣ Run Application

```bash
streamlit run app.py
```

---

## 🎯 Example Queries

* "What are GitLab’s CREDIT values?"
* "How does GitLab handle unlimited PTO?"
* "How should I prepare for a GitLab technical interview?"

---

## 📊 Key Highlights

* Handles **large-scale documentation (75K+ chunks)** efficiently
* Uses **HyDE + Hybrid Retrieval** for better semantic matching
* Reduces hallucinations via **strict grounded generation**
* Designed for **real-world enterprise knowledge systems**

---

## 🚀 Future Improvements

* Add **user authentication & personalization**
* Implement **feedback-based learning loop**
* Integrate **LangGraph / Agents for complex workflows**
* Improve **ranking using rerankers (e.g., cross-encoders)**

---

## 📜 License

This project is for educational and research purposes.

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and share your feedback!
