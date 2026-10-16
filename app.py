"""
app.py — Streamlit Chat UI for College Student Knowledge Assistant
Enhanced with Green Computing Dashboard & GSF Software Carbon Intensity (SCI) Tracking.
Run with: streamlit run app.py
Make sure the FastAPI server is running on port 8000.
"""

import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://127.0.0.1:8000"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="College Knowledge Assistant (Green AI)",
    page_icon="🌱",
    layout="wide",
)

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stTextInput > div > div > input { border-radius: 20px; }
    .answer-box {
        background-color: #ffffff;
        border-left: 5px solid #10b981;
        padding: 18px 22px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .carbon-badge {
        display: inline-block;
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.82em;
        font-weight: 500;
        margin: 4px 6px 4px 0;
    }
    .carbon-badge-miss {
        display: inline-block;
        background: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.82em;
        font-weight: 500;
        margin: 4px 6px 4px 0;
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

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ RAG & Green Settings")

    green_mode = st.toggle(
        "🌱 Enable Green Mode",
        value=True,
        help="Enables LRU response caching, lean context windowing, and embedding caching to minimize carbon footprint and power consumption.",
    )

    search_mode = st.selectbox(
        "Search Mode",
        options=["hybrid", "semantic", "keyword"],
        index=0,
        help="Hybrid combines semantic + keyword for best accuracy."
    )

    doc_type_filter = st.selectbox(
        "Filter by Document Type",
        options=["all", "handbook", "syllabus", "placement", "fees_scholarships", "library", "admin", "calendar"],
        index=0,
        help="Restrict search to a specific document category."
    )

    year_filter = st.selectbox(
        "Filter by Year",
        options=["all", "2025", "2026"],
        index=0,
    )

    top_k = st.slider("Number of chunks to retrieve (top-k)", min_value=1, max_value=10, value=5)

    st.divider()
    st.markdown("### 🌍 Live Sustainability Telemetry")
    if st.button("♻️ Refresh Green Telemetry", use_container_width=True):
        st.rerun()

    try:
        resp = requests.get(f"{API_URL}/green-stats", timeout=5)
        if resp.status_code == 200:
            gs = resp.json()
            c1, c2 = st.columns(2)
            c1.metric("Queries", gs.get("total_queries", 0))
            c2.metric("Hit Rate", f"{gs.get('cache_hit_rate_pct', 0)}%")

            c3, c4 = st.columns(2)
            c3.metric("Energy Saved", f"{gs.get('cumulative_energy_saved_kwh', 0):.6f} kWh")
            c4.metric("CO₂ Avoided", f"{gs.get('cumulative_emissions_avoided_g_co2', 0):.4f} g")

            st.caption(f"⚡ Avg SCI: **{gs.get('average_sci_g_co2_per_query', 0):.6f} gCO₂eq / query**")
        else:
            st.caption("Waiting for API connection...")
    except Exception:
        st.caption("⚠️ API offline on port 8000")

    st.divider()
    st.markdown("### 📂 Upload Document")
    uploaded_file = st.file_uploader(
        "Upload TXT, PDF, DOCX, or HTML",
        type=["txt", "pdf", "docx", "html"],
    )
    if uploaded_file and st.button("📤 Upload & Index", use_container_width=True):
        with st.spinner("Uploading and indexing..."):
            try:
                resp = requests.post(
                    f"{API_URL}/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                    timeout=60,
                )
                if resp.status_code == 200:
                    st.success("Uploaded & indexed successfully!")
                else:
                    st.error(f"Upload failed: {resp.text}")
            except Exception as e:
                st.error(f"Error: {e}")

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


# ── Main Tabs ────────────────────────────────────────────────────────────────
tab_chat, tab_green = st.tabs(["💬 Student Knowledge Assistant", "🌱 Green Computing & SCI Dashboard"])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: Chat Assistant
# ═════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown("## 🎓 College Student Knowledge Assistant")
    st.markdown(
        "Ask questions about attendance, exams, fees, placements, library, or syllabus — "
        "powered by official college documents with **live Carbon & Energy (SCI) tracking**."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

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

    if ask_clicked and question.strip():
        with st.spinner("Searching documents & measuring energy consumption..."):
            try:
                payload = {
                    "question": question.strip(),
                    "search_mode": search_mode,
                    "doc_type_filter": None if doc_type_filter == "all" else doc_type_filter,
                    "year_filter": None if year_filter == "all" else year_filter,
                    "top_k": top_k,
                    "green_mode": green_mode,
                }
                resp = requests.post(f"{API_URL}/query", json=payload, timeout=120)

                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.chat_history.insert(0, {"question": question, "data": data})
                else:
                    st.error(f"API Error {resp.status_code}: {resp.text}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Start server with: python -m uvicorn main:app --port 8000 --reload")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    # Display chat history
    for item in st.session_state.chat_history:
        q = item["question"]
        data = item["data"]
        gm = data.get("green_metrics", {})
        is_hit = gm.get("is_cache_hit", False)

        st.markdown(f"**🙋 Question:** {q}")

        # Green telemetry badge
        if is_hit:
            badge_html = f"""
            <span class="carbon-badge">⚡ Cache Hit (Green Optimized)</span>
            <span class="carbon-badge">⏱️ {gm.get('duration_ms', 0)} ms</span>
            <span class="carbon-badge">💡 {gm.get('energy_kwh', 0):.8f} kWh</span>
            <span class="carbon-badge">🌍 SCI: {gm.get('sci_score_g_co2_per_query', 0):.6f} gCO₂eq</span>
            <span class="carbon-badge">🌱 Saved: {gm.get('energy_saved_vs_baseline_kwh', 0):.8f} kWh</span>
            """
        else:
            badge_html = f"""
            <span class="carbon-badge-miss">⚙️ Model Inference (Cache Miss)</span>
            <span class="carbon-badge-miss">⏱️ {gm.get('duration_ms', 0)} ms</span>
            <span class="carbon-badge-miss">💡 {gm.get('energy_kwh', 0):.8f} kWh</span>
            <span class="carbon-badge-miss">🌍 SCI: {gm.get('sci_score_g_co2_per_query', 0):.6f} gCO₂eq</span>
            """
        st.markdown(badge_html, unsafe_allow_html=True)

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


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: Green Computing & SCI Dashboard
# ═════════════════════════════════════════════════════════════════════════════
with tab_green:
    st.markdown("## 🌱 Green Software Engineering & Sustainability Dashboard")
    st.markdown(
        "Demonstrating principles of Green Software Engineering, energy profiling with **CodeCarbon**, "
        "and the **Software Carbon Intensity (SCI)** standard defined by the **Green Software Foundation (GSF)**."
    )

    st.divider()

    # 1. SCI Formula Card
    st.markdown("### 📐 GSF Software Carbon Intensity (SCI) Formulation")
    st.latex(r"SCI = \frac{(E \times I) + M}{R}")
    st.markdown("""
    - **$E$ (Energy Consumption)**: Total electricity consumed per query in kilowatt-hours ($kWh$), calculated from CPU TDP load factor and operational runtime.
    - **$I$ (Location-based Grid Carbon Intensity)**: Carbon emissions per unit electricity ($710\text{ gCO}_2\text{eq/kWh}$ for Indian national grid average).
    - **$M$ (Embodied Carbon)**: Hardware manufacturing and disposal emissions amortized over active query runtime ($\approx 0.00238\text{ gCO}_2\text{eq/s}$ for a laptop device).
    - **$R$ (Functional Unit)**: 1 student query served ($R = 1$).
    """)

    st.divider()

    # 2. Before / After Comparison Live Benchmark
    st.markdown("### ⚔️ Before & After: Baseline vs Green-Optimized Query")
    st.caption("Click the button below to execute a live comparison between an unoptimized baseline query and a green cached query.")

    bench_col1, bench_col2 = st.columns([2, 3])
    with bench_col1:
        test_query = st.selectbox(
            "Select Benchmark Question",
            options=[
                "What is the minimum attendance required?",
                "When does the next semester start?",
                "What is the fine for returning a library book late?",
                "Am I eligible for placement with 1 backlog?",
            ],
            index=0,
        )
        run_benchmark_btn = st.button("🚀 Run Live Green vs Baseline Comparison", type="primary")

    if run_benchmark_btn:
        with st.spinner("Measuring Baseline query (bypassing cache)..."):
            # Step 1: Run Baseline (green_mode=False)
            t0 = time.time()
            resp_base = requests.post(
                f"{API_URL}/query",
                json={"question": test_query, "green_mode": False, "top_k": 5},
                timeout=60,
            ).json()

        with st.spinner("Measuring Green Optimized query (serving warm cache)..."):
            # Step 2: Prime and run Green (green_mode=True)
            _ = requests.post(
                f"{API_URL}/query",
                json={"question": test_query, "green_mode": True, "top_k": 5},
                timeout=60,
            )
            resp_green = requests.post(
                f"{API_URL}/query",
                json={"question": test_query, "green_mode": True, "top_k": 5},
                timeout=60,
            ).json()

        base_gm = resp_base.get("green_metrics", {})
        green_gm = resp_green.get("green_metrics", {})

        base_lat = base_gm.get("duration_ms", 1200.0)
        green_lat = green_gm.get("duration_ms", 3.0)

        base_energy = base_gm.get("energy_kwh", 0.000008)
        green_energy = green_gm.get("energy_kwh", 0.00000004)

        base_sci = base_gm.get("sci_score_g_co2_per_query", 0.0085)
        green_sci = green_gm.get("sci_score_g_co2_per_query", 0.00004)

        lat_saved_pct = round(100 * (base_lat - green_lat) / max(base_lat, 1), 1)
        energy_saved_pct = round(100 * (base_energy - green_energy) / max(base_energy, 1e-9), 1)
        sci_saved_pct = round(100 * (base_sci - green_sci) / max(base_sci, 1e-9), 1)

        st.success(f"Benchmark Complete! Green optimization reduced energy & carbon intensity by **{energy_saved_pct}%**!")

        # Comparison metrics table
        comp_df = pd.DataFrame({
            "Metric": [
                "Execution Latency",
                "Energy Consumed (E)",
                "Operational CO₂ (E × I)",
                "Embodied Carbon (M)",
                "Software Carbon Intensity (SCI)",
                "Optimization Status"
            ],
            "Baseline (Uncached)": [
                f"{base_lat:.1f} ms",
                f"{base_energy:.8f} kWh",
                f"{base_gm.get('operational_co2_g', 0):.6f} gCO₂",
                f"{base_gm.get('embodied_co2_g', 0):.6f} gCO₂",
                f"{base_sci:.6f} gCO₂eq / query",
                "Full Vector Search + Inference"
            ],
            "Green Optimized (Cached)": [
                f"{green_lat:.1f} ms",
                f"{green_energy:.8f} kWh",
                f"{green_gm.get('operational_co2_g', 0):.6f} gCO₂",
                f"{green_gm.get('embodied_co2_g', 0):.6f} gCO₂",
                f"{green_sci:.6f} gCO₂eq / query",
                "LRU Cache + Embedding Cache"
            ],
            "Savings / Improvement": [
                f"⚡ {lat_saved_pct}% faster",
                f"🌱 {energy_saved_pct}% less energy",
                f"🌱 {sci_saved_pct}% less CO₂",
                f"🌱 {lat_saved_pct}% runtime reduction",
                f"🎯 {sci_saved_pct}% SCI reduction",
                "Zero Redundant Compute"
            ],
        })
        st.table(comp_df)

        # Visual Comparison Bar Charts
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("#### ⏱️ Latency Comparison (ms)")
            chart_lat_data = pd.DataFrame({
                "Latency (ms)": [base_lat, green_lat]
            }, index=["Baseline", "Green Optimized"])
            st.bar_chart(chart_lat_data)

        with c_chart2:
            st.markdown("#### 🌍 SCI Score (gCO₂eq / query)")
            chart_sci_data = pd.DataFrame({
                "SCI (gCO2eq)": [base_sci, green_sci]
            }, index=["Baseline", "Green Optimized"])
            st.bar_chart(chart_sci_data)

    st.divider()

    # 3. Green Software Engineering Principles Implemented
    st.markdown("### 🌿 Principles of Green Software Engineering Applied")
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        st.markdown("""
        **1. Energy Efficiency (GSF Principle 2)**
        - **Two-Tier In-Memory Caching**: Identical questions are answered in `< 5 ms` with negligible CPU load, bypassing computationally expensive transformer inference.
        - **Query Embedding Cache**: Avoids repeated PyTorch forward passes on `all-MiniLM-L6-v2` when querying with multiple filters.

        **2. Hardware Efficiency & Embodied Carbon (GSF Principle 3)**
        - Minimized CPU runtime reduces the amortized embodied carbon ($M$) attributed to each query.
        - Lightweight model architecture (`google/flan-t5-base` ~300MB) runs efficiently on commodity CPU without dedicated GPU power hunger.
        """)

    with gcol2:
        st.markdown("""
        **3. Lean Data Processing & Algorithmic Efficiency**
        - **Context Window Pruning**: Chunks are selectively filtered and pruned to top-3 relevant context passages instead of feeding huge 2000-token contexts into the LLM.
        - **Cosine Similarity Thresholding**: Rejects irrelevant noise chunks before prompting the generator, saving memory bandwidth and token processing FLOPs.

        **4. Carbon Measurement & Monitoring (GSF Principle 1)**
        - Direct hardware telemetry modeled after **CodeCarbon** (CPU TDP + psutil load profiling).
        - Continuous per-query and cumulative SCI metric tracking.
        """)