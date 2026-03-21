"""
app.py — Streamlit Chat UI for College Student Knowledge Assistant
Run with: streamlit run app.py
Make sure the FastAPI server is also running on port 8000.
"""

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="College Knowledge Assistant",
    page_icon="🎓",
    layout="wide",
)

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    .stTextInput > div > div > input { border-radius: 20px; }
    .answer-box {
        background-color: #ffffff;
        border-left: 5px solid #4CAF50;
        padding: 16px 20px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .citation-box {
        background-color: #f0f4ff;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 6px;
        margin: 6px 0;
        font-size: 0.85em;
    }
    .chunk-box {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        padding: 10px 14px;
        border-radius: 6px;
        margin: 4px 0;
        font-size: 0.82em;
    }
    .tag {
        display: inline-block;
        background: #e8f5e9;
        color: #2e7d32;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75em;
        margin-right: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("## 🎓 College Student Knowledge Assistant")
st.markdown("Ask anything about attendance, exams, fees, placements, library, or syllabus — powered by official college documents.")
st.divider()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Search Settings")

    search_mode = st.selectbox(
        "Search Mode",
        options=["hybrid", "semantic", "keyword"],
        index=0,
        help="Hybrid combines semantic + keyword for best results."
    )

    doc_type_filter = st.selectbox(
        "Filter by Document Type",
        options=["all", "handbook", "syllabus", "placement", "fees_scholarships", "library", "admin", "calendar"],
        index=0,
        help="Restrict search to a specific document type."
    )

    year_filter = st.selectbox(
        "Filter by Year",
        options=["all", "2025", "2026"],
        index=0,
    )

    top_k = st.slider("Number of chunks to retrieve (top-k)", min_value=1, max_value=10, value=5)

    st.divider()
    st.markdown("### 📂 Upload a Document")
    uploaded_file = st.file_uploader(
        "Upload TXT, PDF, DOCX, or HTML",
        type=["txt", "pdf", "docx", "html"],
    )
    if uploaded_file:
        if st.button("📤 Upload & Index"):
            with st.spinner("Uploading and indexing..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        st.success(f"Uploaded successfully!")
                        st.json(resp.json())
                    else:
                        st.error(f"Upload failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    st.markdown("### 📊 System Stats")
    if st.button("Refresh Stats"):
        try:
            resp = requests.get(f"{API_URL}/stats", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                vs = data.get("vector_store", {})
                st.metric("Indexed Chunks", vs.get("total_chunks", "N/A"))
                st.caption(f"Model: {vs.get('embedding_model', 'N/A')}")
            else:
                st.warning("Could not fetch stats.")
        except Exception as e:
            st.error(f"API not reachable: {e}")

    st.divider()
    st.markdown("### 💡 Example Questions")
    examples = [
        "What is the minimum attendance required?",
        "When does the next semester start?",
        "Am I eligible for placement with 1 backlog?",
        "What scholarships are available for 2nd year students?",
        "What is the fine for returning a library book late?",
        "What are the prerequisites for Data Structures?",
        "How do I apply for a bonafide certificate?",
        "What is the late fee rule if I miss the semester fee deadline?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["prefill"] = ex

# ── Chat history ─────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Input box ─────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
question = st.text_input(
    "💬 Ask your question here...",
    value=prefill,
    placeholder="e.g. What is the minimum attendance required to sit for exams?",
    key="question_input",
)

col1, col2 = st.columns([1, 5])
with col1:
    ask_clicked = st.button("🔍 Ask", use_container_width=True, type="primary")
with col2:
    if st.button("🗑️ Clear Chat", use_container_width=False):
        st.session_state.chat_history = []
        st.rerun()

# ── Query ─────────────────────────────────────────────────────────────────────
if ask_clicked and question.strip():
    with st.spinner("Searching documents and generating answer..."):
        try:
            payload = {
                "question": question.strip(),
                "search_mode": search_mode,
                "doc_type_filter": None if doc_type_filter == "all" else doc_type_filter,
                "year_filter": None if year_filter == "all" else year_filter,
                "top_k": top_k,
            }
            resp = requests.post(f"{API_URL}/query", json=payload, timeout=120)

            if resp.status_code == 200:
                data = resp.json()
                st.session_state.chat_history.insert(0, {"question": question, "data": data})
            else:
                st.error(f"API Error {resp.status_code}: {resp.text}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the API. Make sure the FastAPI server is running: python -m uvicorn main:app --port 8000 --reload")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ── Display chat history ──────────────────────────────────────────────────────
for item in st.session_state.chat_history:
    q = item["question"]
    data = item["data"]

    st.markdown(f"**🙋 Question:** {q}")

    st.markdown(f"""
    <div class="answer-box">
        <strong>🤖 Answer:</strong><br><br>{data.get('answer', 'No answer returned.')}
    </div>
    """, unsafe_allow_html=True)

    citations = data.get("citations", [])
    if citations:
        st.markdown("**📚 Sources cited:**")
        for cite in citations:
            st.markdown(f"""
            <div class="citation-box">
                <strong>{cite.get('source', 'Unknown')}</strong>
                <span class="tag">{cite.get('doc_type', '')}</span>
                <span class="tag">{cite.get('year', '')}</span><br>
                <em>{cite.get('snippet', '')}</em>
            </div>
            """, unsafe_allow_html=True)

    with st.expander(f"🔎 View {len(data.get('retrieved_chunks', []))} retrieved chunks"):
        for chunk in data.get("retrieved_chunks", []):
            st.markdown(f"""
            <div class="chunk-box">
                <strong>{chunk.get('filename', '')}</strong>
                <span class="tag">{chunk.get('search_type', '')}</span>
                <span class="tag">score: {chunk.get('score', 'N/A')}</span><br>
                {chunk.get('snippet', '')}
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"<small>🔧 Model: {data.get('model_used', 'N/A')} | Mode: {data.get('search_mode', 'N/A')}</small>", unsafe_allow_html=True)
    st.divider()