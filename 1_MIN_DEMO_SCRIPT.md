# 🎬 1-MINUTE VIDEO DEMONSTRATION SCRIPT
## Project: Green-Optimized College Student Knowledge Assistant

**Target Duration:** Exactly 60 Seconds (1:00)  
**Tools to Record:** OBS Studio, Windows Game Bar (`Win + G`), or Loom  
**Pre-recording Setup (Before pressing record):**
1. Terminal 1: Start FastAPI backend:
   ```powershell
   venv\Scripts\activate
   python -m uvicorn main:app --port 8000 --reload
   ```
2. Terminal 2: Start Streamlit UI:
   ```powershell
   venv\Scripts\activate
   streamlit run app.py
   ```
3. Open browser at `http://localhost:8501`. Have the **💬 Student Knowledge Assistant** tab active.

---

### ⏱️ Second-by-Second Video Timeline

| Time | On-Screen Action | Spoken Voiceover (Read this aloud clearly) |
| :--- | :--- | :--- |
| **0:00 - 0:10** | Show the Streamlit web app title and ask an initial question: *"What is the minimum attendance required?"* Click **🔍 Ask**. | *"Hello! For my Green Software Engineering practical, I transformed my College Student Knowledge Assistant into a green-optimized RAG system with live carbon and energy tracking."* |
| **0:10 - 0:25** | Point mouse to the generated answer and the **Green Carbon Badge** below the question (showing ms, kWh, and SCI score). | *"Here, the system answers student queries using official documents. Notice each response computes the GSF Software Carbon Intensity (SCI) metric in real time using CodeCarbon's processor TDP model."* |
| **0:25 - 0:38** | Ask the **same question again** (or click the example button). Watch it return in **0 ms** with `⚡ Cache Hit (Green Optimized)` badge. | *"When a repeated query is asked, our two-tier LRU caching serves the result in under 1 millisecond at near-idle power, cutting query energy and carbon emissions by over 99%."* |
| **0:38 - 0:52** | Switch to the **🌱 Green Computing & SCI Dashboard** tab. Click **🚀 Run Live Green vs Baseline Comparison**. Show the comparison table and bar charts. | *"Switching to our Green Dashboard, we can run a live benchmark comparing baseline versus green mode. The benchmark reveals verified energy savings of up to 99% on cached queries and double-digit reductions across typical student workloads."* |
| **0:52 - 1:00** | Point to the SCI formula $SCI = ((E \times I) + M) / R$ and sidebar telemetry. Conclude with a smile. | *"By applying Green Software principles, lean context pruning, and SCI tracking, we prove that AI can be fast, accurate, and environmentally sustainable. Thank you!"* |

---

## 💡 Quick Tips for a 10/10 Score:
1. Speak at a steady, confident pace.
2. If recording voiceover with screen, keep your mouse cursor moving to highlight what you're talking about (the Carbon Badge, the Cache Hit, the Charts).
3. If your video is slightly under 1 minute (e.g., 55 seconds), that's perfect. Do not exceed 65 seconds.
