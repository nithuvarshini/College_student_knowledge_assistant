# 🎬 1-MINUTE VIDEO DEMONSTRATION SCRIPT
## Project: Green-Optimized College Student Knowledge Assistant

**Target Duration:** Exactly 60 Seconds (0:00 - 1:00)  
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
| **0:00 - 0:10** | Show the Streamlit web app title. Enter the question: *"What is the minimum attendance required?"* Click **🔍 Ask**. | *"Hello! For my Green Software Engineering practical, I enhanced our College Student Knowledge Assistant with live carbon tracking and green computing optimizations."* |
| **0:10 - 0:25** | Point mouse to the generated answer and the **Green Carbon Badge** below the question (pointing out ms, Measured Energy in kWh, and SCI Score). | *"Here, the assistant answers queries with citations. Each response measures energy using CodeCarbon's task tracker and calculates the GSF Software Carbon Intensity (SCI) metric in real time."* |
| **0:25 - 0:38** | Ask the **same question again** (click the example question or re-click Ask). Watch it return in **~4 ms** with the `⚡ Cache Hit (Green Optimized)` badge. | *"When a repeated question is asked, our two-tier LRU cache serves the verified answer in under 5 milliseconds at idle power, reducing query energy and carbon emissions by over 99%."* |
| **0:38 - 0:50** | Click on the **🌱 Green Computing & SCI Dashboard** tab. Click **🚀 Run Live Green vs Baseline Comparison**. Show the comparison table and bar charts. | *"In the Green Dashboard, we can benchmark baseline versus green mode live. Notice the clear separation of measured energy, operational emissions, and embodied carbon, demonstrating over 20% total energy savings across student workloads."* |
| **0:50 - 1:00** | Point to the SCI formula $SCI = ((E \times I) + M) / R$ and sidebar telemetry. Conclude with a smile. | *"By applying Green Software principles, lean context pruning, and CodeCarbon measurement, we demonstrate sustainable AI engineering. Thank you!"* |

---

## 💡 Quick Tips for a 10/10 Score:
1. Speak at a steady, confident pace.
2. Keep your mouse cursor moving to highlight what you speak about (the Carbon Badge, the Cache Hit, the Comparison Table).
3. Keep the video between 55 and 60 seconds.
