import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag_engine import ask

# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitLab Handbook Assistant",
    page_icon="🦊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* main background */
    .stApp {
        background-color: #0d1117;
    }
    /* chat messages */
    .user-message {
        background: #1c2128;
        border-left: 4px solid #fc6d26;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
        color: #e6edf3;
    }
    .bot-message {
        background: #161b22;
        border-left: 4px solid #6e40c9;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
        color: #e6edf3;
    }
    /* source cards */
    .source-card {
        background: #1c2128;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.85em;
        color: #8b949e;
    }
    .source-handbook {
        border-left: 3px solid #1f6feb;
    }
    .source-direction {
        border-left: 3px solid #3fb950;
    }
    /* input box */
    .stTextInput input {
        background-color: #1c2128 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    /* hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* sidebar */
    .css-1d391kg {
        background-color: #161b22;
    }
</style>
""", unsafe_allow_html=True)

# ── session state ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://about.gitlab.com/images/press/logo/png/gitlab-logo-500.png", width=150)
    st.markdown("## 🦊 GitLab Assistant")
    st.markdown("Ask me anything about GitLab's handbook and product direction.")
    
    st.markdown("---")
    st.markdown("### 💡 Sample Questions")
    
    sample_questions = [
        "What are GitLab's core values?",
        "How does GitLab handle remote work?",
        "What is GitLab's 3 year strategy?",
        "How do I request time off at GitLab?",
        "What is GitLab's hiring process?",
        "What are GitLab's FY26 investment themes?",
    ]
    
    for q in sample_questions:
        if st.button(q, key=q, use_container_width=True):
            st.session_state.pending_question = q

    st.markdown("---")
    st.markdown("### ℹ️ Data Sources")
    st.markdown("📘 **Handbook** — policies, processes, culture")
    st.markdown("🗺️ **Direction** — strategy, roadmap, vision")
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()

# ── main area ──────────────────────────────────────────────────────────────
st.markdown("# 🦊 GitLab Handbook Assistant")
st.markdown("*Powered by Hybrid RAG + HyDE — Ask anything about GitLab*")
st.markdown("---")

# display chat history
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align: center; padding: 60px 0; color: #8b949e;'>
            <h3>👋 Welcome!</h3>
            <p>Ask me anything about GitLab's handbook, culture, processes, or product direction.</p>
            <p>Use the sample questions in the sidebar to get started.</p>
        </div>
        """, unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class='user-message'>
                <strong>👤 You</strong><br>{msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='bot-message'>
                <strong>🦊 GitLab Assistant</strong><br>{msg['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # show sources
            if msg.get("sources"):
                with st.expander(f"📚 View {len(msg['sources'])} sources", expanded=False):
                    for src in msg["sources"]:
                        icon  = "📘" if src["collection"] == "handbook"  else "🗺️"
                        label = "Handbook"  if src["collection"] == "handbook" else "Direction"
                        css   = "source-handbook" if src["collection"] == "handbook" else "source-direction"
                        url   = src.get("url", "")
                        link  = f'<a href="{url}" target="_blank">🔗 View source</a>' if url else ""
                        st.markdown(f"""
                        <div class='source-card {css}'>
                            {icon} <strong>{label}</strong> — {src['source']} 
                            &nbsp;|&nbsp; relevance: {src['score']}
                            &nbsp;{link}
                        </div>
                        """, unsafe_allow_html=True)

# ── input area ─────────────────────────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.text_input(
        "Ask a question...",
        key="user_input",
        placeholder="e.g. What are GitLab's core values?",
        label_visibility="collapsed"
    )
with col2:
    send_clicked = st.button("Send 🚀", use_container_width=True)

# handle sidebar sample question clicks
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question
    send_clicked = True

# ── process question ───────────────────────────────────────────────────────
if send_clicked and user_input and user_input.strip():
    # add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # show spinner while thinking
    with st.spinner("🔍 Searching handbook and direction pages..."):
        try:
            result = ask(user_input, st.session_state.chat_history)
            answer  = result["answer"]
            sources = result["sources"]

            # add bot message
            st.session_state.messages.append({
                "role":    "assistant",
                "content": answer,
                "sources": sources
            })

            # update chat history for context
            st.session_state.chat_history.append({
                "user":      user_input,
                "assistant": answer
            })

        except Exception as e:
            st.session_state.messages.append({
                "role":    "assistant",
                "content": f"⚠️ Error: {str(e)}. Please try again.",
                "sources": []
            })

    st.rerun()

# ── footer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align: center; color: #8b949e; font-size: 0.8em; padding: 20px 0;'>
    Built with ❤️ using Hybrid RAG + HyDE | 
    Data from GitLab Handbook & Direction Pages |
    Powered by Gemini + Sentence Transformers
</div>
""", unsafe_allow_html=True)