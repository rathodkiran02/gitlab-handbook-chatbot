import streamlit as st
import sys
import os
import random
from pathlib import Path
from huggingface_hub import snapshot_download

# ── download chroma_db from Hugging Face if not present ───────────────────
CHROMA_PATH = Path("chroma_db")
if not CHROMA_PATH.exists():
    with st.spinner("🔄 Loading knowledge base... (first time only, ~2 mins)"):
        snapshot_download(
            repo_id="rathod02/gitlab-chatbot-db",
            repo_type="dataset",
            local_dir="chroma_db",
            token=os.getenv("HF_TOKEN")
        )

sys.path.insert(0, str(Path(__file__).parent / "src"))
from rag_engine import ask

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitLab Assistant",
    page_icon="🦊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

GITLAB_FACTS = [
    "🌍 GitLab has team members in 60+ countries — truly all-remote since day one.",
    "📖 GitLab's handbook has over 2,000 pages — one of the most transparent company docs in the world.",
    "🚀 GitLab releases a new version every single month, on the 22nd.",
    "💡 GitLab was founded in 2011 by Dmitriy Zaporozhets and Sytse 'Sid' Sijbrandij.",
    "🤝 GitLab's values spell CREDIT — Collaboration, Results, Efficiency, Diversity, Iteration, Transparency.",
    "🦊 The tanuki (Japanese raccoon dog) is GitLab's mascot — symbolizing adaptability.",
    "⚡ GitLab CI/CD was one of the first built-in CI/CD systems in a DevOps platform.",
    "🌐 Over 30 million registered users use GitLab worldwide.",
    "📊 GitLab went public on NASDAQ in October 2021 under the ticker GTLB.",
    "🔓 GitLab's core product is open source — anyone can contribute.",
    "💬 GitLab processes over 1 million merge requests every month.",
    "🏆 GitLab was named a Leader in the 2023 Gartner Magic Quadrant for DevOps Platforms.",
]

SUGGESTIONS = [
    "What are GitLab's core values?",
    "How does GitLab handle remote work?",
    "What is GitLab's hiring process?",
    "How do I request time off at GitLab?",
    "How does GitLab approach diversity?",
    "What is GitLab's onboarding process?",
]

THEMES = {
    "light": {
        "label": "☀️ Light",
        "--bg":          "#fafaf8",
        "--surface":     "#ffffff",
        "--border":      "#ebebeb",
        "--text":        "#1a1a1a",
        "--muted":       "#888888",
        "--input-bg":    "#ffffff",
        "--bot-bubble":  "#ffffff",
        "--bot-border":  "#ebebeb",
        "--bot-text":    "#1a1a1a",
        "--pill-bg":     "#f5f5f5",
        "--pill-border": "#e8e8e8",
        "--pill-text":   "#666666",
        "--accent":      "#fc6d26",
        "--accent2":     "#e24329",
        "--shadow":      "rgba(0,0,0,0.06)",
    },
    "dark": {
        "label": "🌙 Dark",
        "--bg":          "#0d1117",
        "--surface":     "#161b22",
        "--border":      "#30363d",
        "--text":        "#e6edf3",
        "--muted":       "#7d8590",
        "--input-bg":    "#1c2128",
        "--bot-bubble":  "#1c2128",
        "--bot-border":  "#30363d",
        "--bot-text":    "#e6edf3",
        "--pill-bg":     "#21262d",
        "--pill-border": "#30363d",
        "--pill-text":   "#8b949e",
        "--accent":      "#fc6d26",
        "--accent2":     "#e24329",
        "--shadow":      "rgba(0,0,0,0.3)",
    },
    "blue": {
        "label": "💙 Blue",
        "--bg":          "#060b18",
        "--surface":     "#0d1526",
        "--border":      "#1a2744",
        "--text":        "#dde5f4",
        "--muted":       "#5a6f96",
        "--input-bg":    "#101e35",
        "--bot-bubble":  "#101e35",
        "--bot-border":  "#1a2744",
        "--bot-text":    "#dde5f4",
        "--pill-bg":     "#131f38",
        "--pill-border": "#1a2744",
        "--pill-text":   "#5a6f96",
        "--accent":      "#4f8ef7",
        "--accent2":     "#2563eb",
        "--shadow":      "rgba(0,0,0,0.4)",
    },
}

# ── session state ─────────────────────────────────────────────────────────────
if "messages"     not in st.session_state: st.session_state.messages     = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "pending_q"    not in st.session_state: st.session_state.pending_q    = None
if "input_key"    not in st.session_state: st.session_state.input_key    = 0
if "theme"        not in st.session_state: st.session_state.theme        = "light"
if "is_loading"   not in st.session_state: st.session_state.is_loading   = False
if "loading_fact" not in st.session_state: st.session_state.loading_fact = ""

t       = THEMES[st.session_state.theme]
is_dark = st.session_state.theme in ("dark","blue")
cv      = "\n".join(f"    {k}: {v};" for k,v in t.items() if k.startswith("--"))

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root {{ {cv} }}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html,body,.stApp{{
    background:var(--bg)!important;
    font-family:'DM Sans',sans-serif!important;
    color:var(--text)!important;
}}
#MainMenu,footer,header,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
[data-testid="stSidebar"],.viewerBadge_container__r5tak{{display:none!important;}}
.block-container{{
    max-width:760px!important;
    padding:0 20px 170px 20px!important;
    margin:0 auto!important;
}}

/* HEADER */
.gl-header{{
    display:flex;align-items:center;gap:14px;
    padding:22px 0 14px 0;
    border-bottom:1px solid var(--border);
    margin-bottom:16px;
    background:var(--bg);
    position:sticky;top:0;z-index:50;
}}
.gl-logo{{
    width:40px;height:40px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    border-radius:11px;
    display:flex;align-items:center;justify-content:center;
    font-size:21px;flex-shrink:0;
    box-shadow:0 4px 14px var(--shadow);
}}
.gl-title{{font-family:'Syne',sans-serif;font-size:1.2em;font-weight:700;color:var(--text);}}
.gl-sub{{font-size:0.77em;color:var(--muted);margin-top:2px;}}
.gl-badge{{
    margin-left:auto;
    background:{'#0a2218' if is_dark else '#f0fdf4'};
    color:#22c55e;
    border:1px solid {'#14532d' if is_dark else '#bbf7d0'};
    border-radius:20px;padding:4px 11px;
    font-size:0.72em;font-weight:500;white-space:nowrap;
}}

/* THEME BUTTONS */
.stButton>button{{
    font-family:'DM Sans',sans-serif!important;
    background:var(--surface)!important;
    color:var(--text)!important;
    border:1px solid var(--border)!important;
    border-radius:9px!important;
    padding:7px 12px!important;
    font-size:0.82em!important;
    height:auto!important;
    line-height:1.4!important;
    width:100%!important;
    white-space:normal!important;
    text-align:left!important;
    transition:all 0.15s ease!important;
    box-shadow:none!important;
}}
.stButton>button:hover{{
    border-color:var(--accent)!important;
    color:var(--accent)!important;
    background:{'#180d05' if is_dark else '#fff8f5'}!important;
    transform:translateY(-1px)!important;
    box-shadow:0 4px 12px var(--shadow)!important;
}}

/* WELCOME */
.welcome{{text-align:center;padding:28px 0 20px 0;}}
.w-emoji{{font-size:3.2em;margin-bottom:10px;}}
.w-title{{
    font-family:'Syne',sans-serif;
    font-size:1.55em;font-weight:700;
    color:var(--text);margin-bottom:7px;
}}
.w-sub{{
    font-size:0.88em;color:var(--muted);
    line-height:1.6;max-width:400px;margin:0 auto 24px;
}}
.sug-label{{
    font-size:0.74em;font-weight:600;
    letter-spacing:0.07em;text-transform:uppercase;
    color:var(--muted);margin-bottom:9px;text-align:left;
}}

/* MESSAGES */
.msg-user{{display:flex;justify-content:flex-end;margin:14px 0;}}
.msg-user-bubble{{
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    color:#fff;
    padding:11px 16px;
    border-radius:18px 18px 4px 18px;
    max-width:78%;font-size:0.92em;line-height:1.55;
    box-shadow:0 4px 16px var(--shadow);
    word-wrap:break-word;
}}
.msg-bot{{display:flex;gap:10px;align-items:flex-start;margin:14px 0;}}
.bot-av{{
    width:32px;height:32px;flex-shrink:0;margin-top:2px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    font-size:15px;
    box-shadow:0 2px 8px var(--shadow);
}}
.bot-bubble{{
    background:var(--bot-bubble);
    border:1px solid var(--bot-border);
    padding:13px 17px;
    border-radius:4px 18px 18px 18px;
    max-width:88%;font-size:0.92em;line-height:1.65;
    box-shadow:0 2px 12px var(--shadow);
    color:var(--bot-text);word-wrap:break-word;
}}
.bot-bubble p{{margin-bottom:8px;}}
.bot-bubble p:last-child{{margin-bottom:0;}}
.bot-bubble ul,.bot-bubble ol{{padding-left:18px;margin:6px 0;}}
.bot-bubble li{{margin-bottom:3px;}}
.bot-bubble strong{{color:var(--accent);}}
.bot-bubble table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:0.88em;}}
.bot-bubble th{{background:var(--surface);padding:7px 11px;text-align:left;border:1px solid var(--border);font-weight:600;}}
.bot-bubble td{{padding:6px 11px;border:1px solid var(--border);}}
.bot-bubble code{{background:var(--surface);padding:1px 6px;border-radius:4px;font-size:0.88em;font-family:monospace;}}

/* SOURCES */
.src-row{{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px;padding-top:10px;border-top:1px solid var(--border);}}
.src-pill{{background:var(--pill-bg);border:1px solid var(--pill-border);border-radius:6px;padding:3px 9px;font-size:0.73em;color:var(--pill-text);}}
.src-pill.hb{{color:#3b82f6;background:{'#0c1d3a' if is_dark else '#eff6ff'};border-color:{'#1d3461' if is_dark else '#bfdbfe'};}}
.src-pill.dr{{color:#22c55e;background:{'#0a2218' if is_dark else '#f0fdf4'};border-color:{'#14532d' if is_dark else '#bbf7d0'};}}

/* LOADING */
.loading-box{{display:flex;gap:10px;align-items:flex-start;margin:14px 0;}}
.loading-bubble{{
    background:var(--bot-bubble);border:1px solid var(--bot-border);
    padding:13px 17px;border-radius:4px 18px 18px 18px;
    font-size:0.88em;color:var(--muted);
    box-shadow:0 2px 12px var(--shadow);min-width:200px;
}}
.dots span{{
    display:inline-block;width:7px;height:7px;
    background:var(--accent);border-radius:50%;margin:0 2px;
    animation:bounce 1.2s infinite ease-in-out;
}}
.dots span:nth-child(2){{animation-delay:.2s;}}
.dots span:nth-child(3){{animation-delay:.4s;}}
@keyframes bounce{{
    0%,80%,100%{{transform:translateY(0);opacity:.4;}}
    40%{{transform:translateY(-6px);opacity:1;}}
}}
.loading-fact{{font-size:0.8em;color:var(--accent);margin-top:8px;font-style:italic;line-height:1.5;opacity:.85;}}

/* INPUT BAR */
.input-bar{{
    position:fixed;bottom:0;left:0;right:0;
    background:var(--bg);
    border-top:1px solid var(--border);
    padding:12px 0 14px 0;z-index:999;
}}
.input-inner{{max-width:760px;margin:0 auto;padding:0 20px;}}
.input-hint{{font-size:0.71em;color:var(--muted);text-align:center;margin-top:5px;}}

.stTextInput>div>div{{
    border:1.5px solid var(--border)!important;
    border-radius:14px!important;
    background:var(--input-bg)!important;
    box-shadow:0 4px 20px var(--shadow)!important;
    transition:border-color 0.2s,box-shadow 0.2s!important;
}}
.stTextInput>div>div:focus-within{{
    border-color:var(--accent)!important;
    box-shadow:0 4px 20px var(--shadow)!important;
}}
.stTextInput input{{
    font-family:'DM Sans',sans-serif!important;
    font-size:0.95em!important;
    color:var(--text)!important;
    padding:13px 18px!important;
    background:transparent!important;
    border:none!important;box-shadow:none!important;
    caret-color:var(--accent)!important;
}}
.stTextInput input::placeholder{{color:var(--muted)!important;opacity:.6!important;}}
.stTextInput input:focus{{box-shadow:none!important;outline:none!important;}}

/* SEND BUTTON — last col in horizontal block */
div[data-testid="stHorizontalBlock"]>div:last-child .stButton>button{{
    background:linear-gradient(135deg,var(--accent),var(--accent2))!important;
    color:#fff!important;border:none!important;
    border-radius:12px!important;
    padding:13px 22px!important;
    font-weight:600!important;font-size:0.93em!important;
    height:50px!important;white-space:nowrap!important;
    box-shadow:0 4px 14px var(--shadow)!important;
    transition:all 0.2s!important;
    text-align:center!important;
}}
div[data-testid="stHorizontalBlock"]>div:last-child .stButton>button:hover{{
    transform:translateY(-2px)!important;
    box-shadow:0 6px 20px var(--shadow)!important;
    background:linear-gradient(135deg,var(--accent2),var(--accent))!important;
    color:#fff!important;border:none!important;
}}

/* expander */
.streamlit-expanderHeader{{font-size:0.78em!important;color:var(--muted)!important;background:transparent!important;padding:4px 0!important;}}
::-webkit-scrollbar{{width:4px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:var(--border);border-radius:4px;}}
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gl-header">
    <div class="gl-logo">🦊</div>
    <div>
        <div class="gl-title">GitLab Assistant</div>
        <div class="gl-sub">Handbook · Direction · Culture · Strategy</div>
    </div>
    <div class="gl-badge">● Online</div>
</div>
""", unsafe_allow_html=True)

# ── THEME ROW ─────────────────────────────────────────────────────────────────
tc = st.columns([1, 1, 1, 5])
for i, (key, th) in enumerate(THEMES.items()):
    with tc[i]:
        if st.button(th["label"], key=f"th_{key}", use_container_width=True):
            st.session_state.theme = key
            st.rerun()

# ── WELCOME + SUGGESTIONS ─────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome">
        <div class="w-emoji">🦊</div>
        <div class="w-title">Hey, I'm your GitLab Assistant!</div>
        <div class="w-sub">Ask me anything about GitLab's culture, values,
        hiring, remote work, product strategy, and more.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sug-label'>Suggested questions</div>",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, q in enumerate(SUGGESTIONS):
        with (c1 if i % 2 == 0 else c2):
            if st.button(q, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_q = q
                st.rerun()

# ── MESSAGES ──────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-user">
            <div class="msg-user-bubble">{msg['content']}</div>
        </div>""", unsafe_allow_html=True)
    else:
        pills = ""
        if msg.get("sources"):
            for s in msg["sources"][:6]:
                cls  = "hb" if s["collection"] == "handbook" else "dr"
                icon = "📘" if cls == "hb" else "🗺️"
                name = s["source"].replace("\\","/").split("/")[-1].replace(".md","")[:26]
                pills += f"<span class='src-pill {cls}'>{icon} {name}</span>"
        src_html = f"<div class='src-row'>{pills}</div>" if pills else ""

        st.markdown(f"""
        <div class="msg-bot">
            <div class="bot-av">🦊</div>
            <div class="bot-bubble">{msg['content']}{src_html}</div>
        </div>""", unsafe_allow_html=True)

        if msg.get("sources"):
            with st.expander(f"📚 {len(msg['sources'])} sources"):
                for s in msg["sources"]:
                    icon  = "📘" if s["collection"] == "handbook" else "🗺️"
                    label = "Handbook" if s["collection"] == "handbook" else "Direction"
                    url   = s.get("url","")
                    st.markdown(f"{icon} **{label}** — {s['source']} `{s.get('score',0)}`")

# ── LOADING BUBBLE ────────────────────────────────────────────────────────────
if st.session_state.is_loading:
    st.markdown(f"""
    <div class="loading-box">
        <div class="bot-av">🦊</div>
        <div class="loading-bubble">
            <div class="dots"><span></span><span></span><span></span></div>
            <div class="loading-fact">💡 {st.session_state.loading_fact}</div>
        </div>
    </div>""", unsafe_allow_html=True)

# ── INPUT BAR ─────────────────────────────────────────────────────────────────
st.markdown("<div class='input-bar'><div class='input-inner'>",
            unsafe_allow_html=True)
col1, col2 = st.columns([6, 1])
with col1:
    user_input = st.text_input(
        "q", key=f"inp_{st.session_state.input_key}",
        placeholder="Ask anything about GitLab... (press Enter to send)",
        label_visibility="collapsed",
    )
with col2:
    send_btn = st.button("Send ↑", use_container_width=True)
st.markdown(
    "<div class='input-hint'>⏎ Enter to send &nbsp;·&nbsp; ⇧⏎ Shift+Enter for new line</div>",
    unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)

# ── HANDLE INPUT ──────────────────────────────────────────────────────────────
if st.session_state.pending_q:
    question = st.session_state.pending_q
    st.session_state.pending_q = None
elif (send_btn or user_input) and user_input and user_input.strip():
    question = user_input.strip()
else:
    question = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.input_key   += 1
    st.session_state.is_loading   = True
    st.session_state.loading_fact = random.choice(GITLAB_FACTS)
    st.rerun()

# ── RUN RAG ───────────────────────────────────────────────────────────────────
if st.session_state.is_loading:
    last_user = next(
        (m["content"] for m in reversed(st.session_state.messages)
         if m["role"] == "user"), None
    )
    if last_user:
        try:
            result  = ask(last_user, st.session_state.chat_history)
            answer  = result["answer"]
            sources = result["sources"]
            st.session_state.messages.append({
                "role": "assistant", "content": answer, "sources": sources
            })
            st.session_state.chat_history.append({
                "user": last_user, "assistant": answer
            })
        except Exception as e:
            err = str(e)
            if "429" in err:
                reply = "⚠️ API quota reached. Please wait a moment and try again."
            elif "503" in err:
                reply = "⚠️ Gemini servers are busy. Please try again in a few seconds."
            else:
                reply = f"⚠️ Something went wrong: {err[:200]}"
            st.session_state.messages.append({
                "role": "assistant", "content": reply, "sources": []
            })
    st.session_state.is_loading = False
    st.rerun()