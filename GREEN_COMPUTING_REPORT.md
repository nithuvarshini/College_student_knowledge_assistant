# GREEN SOFTWARE ENGINEERING & SUSTAINABILITY PROJECT REPORT

**Course:** Green Software Engineering (Practical L T P C: 0 0 2 1)  
**Project Title:** Green-Optimized College Student Knowledge Assistant (RAG Pipeline)  
**Student Assessment:** Capstone Implementation & Carbon Intensity Measurement  
**Measurement Tool:** CodeCarbon & Green Software Foundation (GSF) SCI Standard  
**Date:** October 2026  

---

## 1. Executive Summary & Objective

Modern Retrieval-Augmented Generation (RAG) and Large Language Model (LLM) workflows are notoriously energy-intensive due to repetitive tensor floating-point operations (FLOPs), redundant vector similarity scans, and high CPU/GPU power consumption. 

In this project, the **College Student Knowledge Assistant** was enhanced with **Green Software Engineering** principles to achieve substantial operational energy savings, lower hardware utilization, and reduced carbon emissions without sacrificing retrieval quality or answer accuracy.

### Key Highlights:
- **Energy Optimization:** Implemented two-tier caching (LRU Response Caching and Sentence-Transformer Embedding Caching) and lean context window pruning.
- **Empirical Measurement:** Integrated **CodeCarbon** and real-time hardware CPU power telemetry (TDP load profiling).
- **GSF SCI Metric:** Implemented the formal **Software Carbon Intensity (SCI)** equation ($\text{gCO}_2\text{eq}$ per query) defined by the Green Software Foundation.
- **Verified Results:** Demonstrated **9.85% overall energy reduction** and **13.84% SCI reduction** across a mixed 10-query student workload, with **99.9% energy savings on repeated queries** ($< 0.01\text{ ms}$ latency vs $\sim 3500\text{ ms}$ uncached).

---

## 2. Alignment with Course Outcomes & Syllabus

| Course Outcome / Unit | Implementation in Project |
| :--- | :--- |
| **CO1: Principles of Green Software** | Applied GSF 8 Principles (Principles 1, 2, 3, and 6) to eliminate redundant neural inference and model amortized embodied emissions ($M$). |
| **CO2: Carbon Measurement Tools** | Integrated **CodeCarbon** to profile processor TDP (15.0W), monitor active load, and quantify electricity consumption ($kWh$). |
| **CO3: Software Carbon Intensity (SCI)** | Modeled and computed the official GSF SCI metric: $SCI = \frac{(E \times I) + M}{R}$ per student query. |
| **Green SDLC & Lean Algorithms** | Context truncation to top-3 relevant passages, similarity threshold filtering, and two-tier in-memory caching. |

---

## 3. Green Computing Concepts & Techniques Introduced

### 3.1 Two-Tier In-Memory Caching (GSF Principle 2: Energy Efficiency)
- **Problem:** Students regularly ask identical high-frequency questions (e.g., *"What is the minimum attendance required?"*, *"When does the next semester start?"*). A standard RAG pipeline executes full vector embeddings and LLM autoregressive text generation for every single request, needlessly running the CPU at 80–100% capacity.
- **Green Solution:**
  1. **Tier-1 Response Cache (LRU):** Stores verified student responses keyed on `(query, search_mode, filter, top_k)`. Serves identical queries in $<0.01\text{ ms}$ at near-idle processor power ($\approx 3.5\text{ W}$ vs $18.5\text{ W}$).
  2. **Tier-2 Query Embedding Cache:** Caches 384-dimensional dense vectors from `sentence-transformers/all-MiniLM-L6-v2`, eliminating redundant PyTorch neural forward passes when students toggle filters or search modes.

### 3.2 Lean Context Processing & Algorithmic Pruning (GSF Principle 3: Hardware Efficiency)
- Excessive prompt tokens increase transformer memory bandwidth and computation quadrically in self-attention layers.
- Context is dynamically pruned to the top-3 most relevant document chunks with strict cosine similarity filtering ($\text{distance} \le 0.50$), reducing prompt token count by $>50\%$.

### 3.3 Dynamic Green Mode Toggle
- Users can switch between **Baseline Mode** (unoptimized full neural pipeline) and **Green Optimized Mode** directly from the UI or API (`"green_mode": true/false`), allowing real-time before/after energy and carbon comparisons.

---

## 4. Carbon & SCI Measurement Methodology

### 4.1 The GSF Software Carbon Intensity (SCI) Specification

The standard SCI equation is defined as:

$$\mathbf{SCI = \frac{(E \times I) + M}{R}}$$

Where:
- **$E$ (Operational Energy in $kWh$):**
  $$E = \frac{P_{\text{active}} \times t}{3,600,000}$$
  Where $P_{\text{active}}$ is total power draw in Watts ($P_{\text{idle}} + \text{TDP} \times \text{load factor} + P_{\text{RAM}}$) and $t$ is execution duration in seconds.
- **$I$ (Location-based Grid Carbon Intensity in $\text{gCO}_2\text{eq}/kWh$):**
  Set to $710.0\text{ gCO}_2\text{eq}/kWh$ in accordance with the Central Electricity Authority (CEA) baseline for the Indian National Grid.
- **$M$ (Embodied Carbon Allocation in $\text{gCO}_2\text{eq}$):**
  Embodied emissions of the host machine amortized over runtime. For a standard laptop ($\sim 300\text{ kg CO}_2\text{eq}$ embodied footprint over a 4-year lifespan):
  $$M_{\text{rate}} = \frac{300,000\text{ g}}{4 \times 365 \times 24 \times 3600\text{ s}} \approx 0.00238\text{ gCO}_2\text{eq/s}$$
  $$M = M_{\text{rate}} \times t$$
- **$R$ (Functional Unit):**
  Defined as **1 student inquiry served** ($R = 1$).

### 4.2 Hardware Telemetry & CodeCarbon Configuration
- **Processor:** Intel(R) Core(TM) i5-6300U CPU @ 2.40GHz (2 Cores, 4 Logical Processors)
- **CPU TDP:** 15.0 Watts (detected via CodeCarbon TDP database)
- **RAM Power:** 2.5 Watts
- **Idle Baseline:** 3.5 Watts

---

## 5. Verified Empirical Benchmark Results

The benchmark test (`benchmark_green.py`) was executed across 10 realistic student questions (with 3 repeated queries, simulating typical 30% cache hit traffic). 

> **Note:** All figures below are directly extracted from verified execution logs (`green_benchmark_results.json`).

| Metric | Baseline (Uncached) | Green Optimized (Cached) | Measured Improvement |
| :--- | :--- | :--- | :--- |
| **Total Workload Duration** | 35.42 seconds | 28.67 seconds | **19.08% faster** |
| **Average Query Latency** | 3541.8 ms | 2866.0 ms | **19.08% reduction** |
| **Total Energy Consumed ($E$)** | 0.00015569 kWh | 0.00014036 kWh | **9.85% energy saved** |
| **Total Cumulative Carbon ($SCI$)** | 0.194838 $\text{gCO}_2\text{eq}$ | 0.167867 $\text{gCO}_2\text{eq}$ | **13.84% carbon saved** |
| **Average SCI per Query** | 0.019484 $\text{gCO}_2\text{eq}$ | 0.016787 $\text{gCO}_2\text{eq}$ | **13.84% reduction** |
| **Cache Hit Performance (Queries 8–10)** | $\approx 2428.3\text{ ms}$ | **$< 0.01\text{ ms}$** | **$> 99.99\%$ latency reduction** |
| **Cache Hit Energy (Queries 8–10)** | $\approx 0.0000107\text{ kWh}$ | **$\approx 0.0000000\text{ kWh}$** | **$> 99.8\%$ energy reduction** |

---

## 6. Software Architecture & Files Modified

```
College-Student-Knowledge-Assistant/
├── main.py                     # Updated with green_mode toggle & /green-stats API
├── app.py                      # Streamlit UI with Carbon Analytics & SCI Dashboard
├── requirements.txt            # Added codecarbon>=3.0.0
├── benchmark_green.py          # Standalone benchmark test runner & verifier
├── green_benchmark_results.json# Verified measured empirical data
├── src/
│   ├── green_tracker.py        # [NEW] CodeCarbon profiling & GSF SCI metric engine
│   ├── generator.py            # Lean prompt context & direct Seq2Seq inference
│   ├── vectorstore.py          # Query embedding cache & cosine filtering
│   ├── rag_pipeline.py         # Green orchestrator with two-tier caching & telemetry
│   └── loader.py / chunker.py  # Document ingestion & pre-chunking
└── documents/                  # Official college circulars and regulations
```

---

## 7. Viva Voce Preparation & Key Concepts

**Q1: What is the Software Carbon Intensity (SCI) metric?**  
*Answer:* SCI is a specification by the Green Software Foundation to score software carbon intensity per functional unit: $SCI = ((E \times I) + M) / R$. Unlike offsetting, SCI focuses on eliminating emissions through better software architecture and operational efficiency.

**Q2: How does CodeCarbon measure energy?**  
*Answer:* CodeCarbon tracks energy consumption by interfacing with hardware sensors (Intel RAPL, Apple Powermetrics, NVIDIA NVML). On platforms without direct sensor access, it uses CPU TDP lookup combined with real-time OS load factors and memory power modeling.

**Q3: Why does in-memory response caching reduce emissions so drastically?**  
*Answer:* Running a transformer model requires billions of CPU/GPU floating point operations, keeping processor cores at 80–100% TDP. Caching returns the precomputed answer in $<0.01\text{ ms}$ at idle power, avoiding $>99\%$ of the operational energy.

**Q4: What is the difference between Operational Carbon ($E \times I$) and Embodied Carbon ($M$)?**  
*Answer:* Operational carbon is the emissions caused by the electricity consumed while running the software ($E \times I$). Embodied carbon ($M$) represents the greenhouse gas emissions from manufacturing, transporting, and disposing of the computer hardware, allocated across the active execution lifespan.

---

## 8. Conclusion

By integrating **Green Software Engineering** principles into the College Student Knowledge Assistant, this project demonstrated that AI applications can be made substantially more sustainable through lean software design. Using **CodeCarbon** and the **GSF SCI** standard, the system reliably quantifies its environmental footprint and achieves double-digit carbon reductions while improving response times for student users.
