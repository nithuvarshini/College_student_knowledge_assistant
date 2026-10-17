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
            st.caption(
                f"🔬 **Energy Accounting:**<br>"
                f"• Directly Tracked: `{gs.get('cumulative_directly_measured_kwh', 0):.8f} kWh`<br>"
                f"• Modeled Estimates: `{gs.get('cumulative_modeled_energy_kwh', 0):.8f} kWh`",
                unsafe_allow_html=True,
            )
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
        dur = gm.get("duration_ms", 0)
        is_measured = gm.get("energy_is_directly_measured", False)
        energy = gm.get("energy_kwh")
        sci = gm.get("sci_score_g_co2_per_query")
        saved_dict = gm.get("savings_vs_last_uncached")
        saved = saved_dict.get("energy_saved_kwh") if isinstance(saved_dict, dict) else gm.get("energy_saved_vs_baseline_kwh")

        cls_tag = "carbon-badge" if is_hit else "carbon-badge-miss"

        if energy is not None:
            if is_measured:
                energy_badge = f'<span class="{cls_tag}">💡 Tracked Energy (CodeCarbon): {energy:.8f} kWh</span>'
            else:
                energy_badge = f'<span class="{cls_tag}">💡 Modeled Energy (Idle Baseline): {energy:.8f} kWh</span>'
        else:
            energy_badge = f'<span class="{cls_tag}">💡 Energy: Unavailable</span>'

        if sci is not None:
            sci_badge = f'<span class="{cls_tag}">🌍 SCI Score: {sci:.6f} gCO₂eq</span>'
        else:
            sci_badge = f'<span class="{cls_tag}">🌍 SCI Score: Unavailable</span>'

        if is_hit:
            saved_badge = f'<span class="carbon-badge">🌱 Energy Saved: {saved:.8f} kWh</span>' if (saved is not None and saved > 0) else ''
            badge_html = f"""
            <span class="carbon-badge">⚡ Cache Hit (Green Optimized)</span>
            <span class="carbon-badge">⏱️ {dur} ms</span>
            {energy_badge}
            {sci_badge}
            {saved_badge}
            """
        else:
            badge_html = f"""
            <span class="carbon-badge-miss">⚙️ Model Inference (Cache Miss)</span>
            <span class="carbon-badge-miss">⏱️ {dur} ms</span>
            {energy_badge}
            {sci_badge}
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
        try:
            with st.spinner("Executing Baseline query (cache disabled)..."):
                r_base = requests.post(
                    f"{API_URL}/query",
                    json={"question": test_query, "green_mode": False, "top_k": 5},
                    timeout=90,
                )
                if r_base.status_code != 200:
                    st.error(f"Baseline query failed: {r_base.status_code} - {r_base.text}")
                    st.stop()
                resp_base = r_base.json()

            with st.spinner("Executing Green query (priming and querying warm cache)..."):
                # Prime the cache with green_mode=True
                _ = requests.post(
                    f"{API_URL}/query",
                    json={"question": test_query, "green_mode": True, "top_k": 5},
                    timeout=90,
                )
                r_green = requests.post(
                    f"{API_URL}/query",
                    json={"question": test_query, "green_mode": True, "top_k": 5},
                    timeout=90,
                )
                if r_green.status_code != 200:
                    st.error(f"Green query failed: {r_green.status_code} - {r_green.text}")
                    st.stop()
                resp_green = r_green.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to FastAPI server at {API_URL}: {e}")
            st.stop()

        base_gm = resp_base.get("green_metrics") or {}
        green_gm = resp_green.get("green_metrics") or {}

        if not base_gm and not green_gm:
            st.error("Green metrics unavailable in server response. Please verify that the API is running with sustainability tracking enabled.")
            st.stop()

        base_lat = base_gm.get("duration_ms")
        green_lat = green_gm.get("duration_ms")
        base_energy = base_gm.get("energy_kwh")
        green_energy = green_gm.get("energy_kwh")
        base_op = base_gm.get("operational_co2_g")
        green_op = green_gm.get("operational_co2_g")
        base_emb = base_gm.get("embodied_co2_g")
        green_emb = green_gm.get("embodied_co2_g")
        base_sci = base_gm.get("sci_score_g_co2_per_query")
        green_sci = green_gm.get("sci_score_g_co2_per_query")

        # Latency calculation
        if base_lat is not None and green_lat is not None and base_lat > 0:
            lat_saved_pct = round(100 * (base_lat - green_lat) / base_lat, 1)
            lat_impact = f"⚡ {lat_saved_pct}% faster"
        else:
            lat_saved_pct = None
            lat_impact = "Unavailable"

        # Energy calculation
        if base_energy is not None and green_energy is not None and base_energy > 0:
            energy_saved_pct = round(100 * (base_energy - green_energy) / base_energy, 1)
            energy_impact = f"🌱 {energy_saved_pct}% less energy"
        else:
            energy_saved_pct = None
            energy_impact = "Unavailable (No valid energy measurement)"

        # Operational CO2 calculation
        if base_op is not None and green_op is not None and base_op > 0:
            op_saved_pct = round(100 * (base_op - green_op) / base_op, 1)
            op_impact = f"🌱 {op_saved_pct}% less operational CO₂"
        else:
            op_impact = "Unavailable"

        # Embodied Carbon calculation
        if lat_saved_pct is not None:
            emb_impact = f"🌱 {lat_saved_pct}% runtime reduction"
        else:
            emb_impact = "Unavailable"

        # SCI Score calculation
        if base_sci is not None and green_sci is not None and base_sci > 0:
            sci_saved_pct = round(100 * (base_sci - green_sci) / base_sci, 1)
            sci_impact = f"🎯 {sci_saved_pct}% SCI reduction"
        else:
            sci_saved_pct = None
            sci_impact = "Unavailable (No valid SCI measurement)"

        # Banner message
        if energy_saved_pct is not None and sci_saved_pct is not None:
            st.success(f"Benchmark Complete! Calculated reduction: **{energy_saved_pct}% energy** and **{sci_saved_pct}% carbon intensity**.")
        else:
            st.warning("⚠️ Benchmark complete, but valid energy/carbon metrics could not be fully verified for both queries. Savings cannot be claimed.")

        base_meas_type = (
            "Directly Tracked (CodeCarbon)"
            if base_gm.get("energy_is_directly_measured")
            else ("Modeled Estimate (Sensor Fallback)" if base_energy is not None else "Unavailable")
        )
        green_meas_type = (
            "Directly Tracked (CodeCarbon)"
            if green_gm.get("energy_is_directly_measured")
            else ("Modeled Estimate (Sub-ms Cache Hit)" if green_energy is not None else "Unavailable")
        )

        # Comparison metrics table
        comp_df = pd.DataFrame({
            "Metric Category": [
                "Execution Latency",
                "Workload Energy (E)",
                "Energy Measurement Source",
                "Operational CO₂ (E × I)",
                "Assumed Embodied Carbon (M)",
                "Software Carbon Intensity (SCI)",
                "Execution Path"
            ],
            "Baseline (Uncached)": [
                f"{base_lat:.1f} ms" if base_lat is not None else "Unavailable",
                f"{base_energy:.10f} kWh" if base_energy is not None else "Unavailable",
                base_meas_type,
                f"{base_op:.8f} gCO₂eq" if base_op is not None else "Unavailable",
                f"{base_emb:.8f} gCO₂eq" if base_emb is not None else "Unavailable",
                f"{base_sci:.8f} gCO₂eq / query" if base_sci is not None else "Unavailable",
                "Full Vector Search + Inference"
            ],
            "Green Optimized (Cached)": [
                f"{green_lat:.1f} ms" if green_lat is not None else "Unavailable",
                f"{green_energy:.10f} kWh" if green_energy is not None else "Unavailable",
                green_meas_type,
                f"{green_op:.8f} gCO₂eq" if green_op is not None else "Unavailable",
                f"{green_emb:.8f} gCO₂eq" if green_emb is not None else "Unavailable",
                f"{green_sci:.8f} gCO₂eq / query" if green_sci is not None else "Unavailable",
                "Two-Tier LRU Cache Hit"
            ],
            "Comparison Impact": [
                lat_impact,
                energy_impact,
                "—",
                op_impact,
                emb_impact,
                sci_impact,
                "Zero Redundant Neural Inference"
            ],
        })
        st.table(comp_df)

        # Visual Comparison Bar Charts
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("#### ⏱️ Latency Comparison (ms)")
            if base_lat is not None and green_lat is not None:
                chart_lat_data = pd.DataFrame({
                    "Latency (ms)": [base_lat, green_lat]
                }, index=["Baseline", "Green Optimized"])
                st.bar_chart(chart_lat_data)
            else:
                st.info("Latency chart unavailable.")

        with c_chart2:
            st.markdown("#### 🌍 SCI Score (gCO₂eq / query)")
            if base_sci is not None and green_sci is not None:
                chart_sci_data = pd.DataFrame({
                    "SCI (gCO2eq)": [base_sci, green_sci]
                }, index=["Baseline", "Green Optimized"])
                st.bar_chart(chart_sci_data)
            else:
                st.info("SCI chart unavailable.")

        st.caption(
            "ℹ️ **Measurement Methodology & Limitations:** "
            "Baseline queries with active inference are directly tracked using CodeCarbon task monitoring. "
            "Sub-millisecond cache hits fall below physical sensor polling frequency and are modeled using the idle baseline power. "
            "Operational CO₂ applies CodeCarbon's India grid intensity (~713 gCO₂eq/kWh). "
            "Embodied carbon (M) is an amortized model estimate per GSF guidelines (300kg CO₂eq / 4-yr lifespan). "
            "Network transmission and external data center PUE are excluded from this local endpoint boundary."
        )

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