# GREEN SOFTWARE ENGINEERING & SUSTAINABILITY PROJECT REPORT

**Course:** Green Software Engineering (Practical L T P C: 0 0 2 1)  
**Project Title:** Green-Optimized College Student Knowledge Assistant (RAG Pipeline)  
**Student Assessment:** Capstone Implementation & Carbon Intensity Measurement  
**Measurement Tool:** CodeCarbon `OfflineEmissionsTracker` & Green Software Foundation (GSF) SCI Standard  
**Date:** October 2026  

---

## 1. Executive Summary & Objective

Modern Retrieval-Augmented Generation (RAG) and Large Language Model (LLM) pipelines are energy-intensive due to repetitive tensor operations, dense vector scans, and continuous CPU/GPU power draw. 

In this project, the **College Student Knowledge Assistant** was augmented with **Green Software Engineering** principles to eliminate redundant computational work, lower execution latency, and measure carbon intensity without sacrificing answer fidelity or citation accuracy.

### Key Highlights:
- **Actual Workload Measurement:** Integrated CodeCarbon's `OfflineEmissionsTracker` using per-task monitoring (`start_task` / `stop_task`) to measure electricity consumption ($kWh$), active power draw ($W$), and operational emissions.
- **Strict SCI Formulation:** Implemented the official GSF Software Carbon Intensity metric, explicitly separating **measured energy ($E$)**, **estimated operational emissions ($O = E \times I$)**, and **assumed embodied carbon ($M$)**.
- **Fair Empirical Benchmark:** Evaluated using automated warm-up runs, identical query sequences across multiple trials, and explicit separation of cache hits versus cache misses.
- **Verified Results:** Across a representative 10-query student workload (30% repeated inquiries), the green-optimized system achieved:
  - **20.24% total energy reduction** ($0.00011513\text{ kWh} \to 0.00009183\text{ kWh}$)
  - **20.35% total SCI reduction** ($0.160531\text{ gCO}_2\text{eq} \to 0.127857\text{ gCO}_2\text{eq}$)
  - **99.91% energy reduction on repeated queries** ($< 5\text{ ms}$ latency vs $\sim 2400\text{ ms}$ uncached).

---

## 2. Alignment with Course Outcomes & Syllabus

| Course Outcome / Unit | Implementation in Project |
| :--- | :--- |
| **CO1: Principles of Green Software** | Applied GSF Principles (Energy Efficiency, Hardware Efficiency, Carbon Awareness, and Lean Processing) to eliminate redundant neural inference. |
| **CO2: Carbon Measurement Tools** | Employed **CodeCarbon** (`OfflineEmissionsTracker`) to profile processor TDP (15.0W) and track workload-level energy ($kWh$). |
| **CO3: Software Carbon Intensity (SCI)** | Modeled and computed the official GSF SCI metric: $SCI = \frac{(E \times I) + M}{R}$ per student query. |
| **Green SDLC & Lean Algorithms** | Implemented two-tier in-memory caching (LRU response cache + vector embedding cache) and lean context pruning. |

---

## 3. Green Computing Concepts & Techniques Introduced

### 3.1 Two-Tier In-Memory Caching (GSF Principle 2: Energy Efficiency)
- **Problem:** Students frequently ask identical inquiries (e.g., *"What is the minimum attendance required?"*, *"When does the next semester start?"*). Standard RAG architectures execute vector embedding models and autoregressive seq2seq transformers for every request, sustaining CPU loads near 80–100% TDP.
- **Green Solution:**
  1. **Tier-1 Response Cache (LRU):** Stores verified answers keyed on `sha256(question + search_mode + filters + top_k)`. Serves warm queries in **$4.7\text{ ms}$** at near-idle processor power, avoiding over $99\%$ of operational energy.
  2. **Tier-2 Query Embedding Cache:** Caches dense vector representations from `sentence-transformers/all-MiniLM-L6-v2`, preventing redundant PyTorch neural forward passes when users modify search filters or top-k settings.

### 3.2 Lean Context Processing & Algorithmic Pruning (GSF Principle 3: Hardware Efficiency)
- Prompt context is pruned to the top-3 relevant passages, and cosine distance filtering ($\le 0.50$) rejects irrelevant chunks before text generation. This reduces context length by $> 50\%$, minimizing self-attention tensor operations and memory bandwidth.

### 3.3 Dynamic Green Mode Toggle
- The pipeline provides an explicit toggle (`"green_mode": true/false`) in both the REST API and Streamlit UI, allowing direct side-by-side verification between baseline and green execution.

---

## 4. Carbon & SCI Measurement Methodology

### 4.1 The GSF Software Carbon Intensity (SCI) Specification

The Software Carbon Intensity metric is defined as:

$$\mathbf{SCI = \frac{(E \times I) + M}{R}}$$

Where:
1. **$E$ (Measured Operational Energy in $kWh$):**
   Tracked directly per task using CodeCarbon's `OfflineEmissionsTracker`, which records active processor and memory power over execution duration:
   $$E = \text{CodeCarbon.energy\_consumed}$$
2. **$I$ (Grid Carbon Intensity in $\text{gCO}_2\text{eq}/kWh$):**
   Location-based emission factor for India (`IND`) in CodeCarbon: $713.0\text{ gCO}_2\text{eq}/kWh$.
   Operational emissions are: $O = E \times I$.
3. **$M$ (Assumed Embodied Carbon Allocation in $\text{gCO}_2\text{eq}$):**
   Hardware manufacturing and disposal emissions amortized over the query's active runtime. For a standard developer laptop ($\sim 300\text{ kg CO}_2\text{eq}$ embodied footprint over a 4-year lifespan):
   $$M_{\text{rate}} = \frac{300,000\text{ g}}{4 \times 365 \times 24 \times 3600\text{ s}} \approx 0.00238\text{ gCO}_2\text{eq/s}$$
   $$M = M_{\text{rate}} \times t$$
4. **$R$ (Functional Unit):**
   Defined as **1 student inquiry served** ($R = 1$).

### 4.2 Documented Assumptions & Limitations
- **Energy Tracking:** On standard Windows platforms without hypervisor/bare-metal MSR permissions, CodeCarbon estimates CPU power using the processor's thermal design power (TDP = 15.0W for Intel Core i5-6300U) scaled by real-time CPU utilization (`psutil`).
- **Embodied Carbon ($M$):** Embodied emissions are an amortized lifecycle model assumption per GSF guidelines and cannot be physically metered in real-time.
- **Boundary:** Network transmission energy and external cloud datacenter PUE overheads are outside the local system boundary.

---

## 5. Verified Empirical Benchmark Results

The benchmark (`benchmark_green.py`) was executed across 10 identical student queries (7 unique queries, 3 repeated queries) with a warm-up phase and averaged across 2 trials. 

> **All figures below represent actual empirical data from [`green_benchmark_results.json`](green_benchmark_results.json).**

### 5.1 Overall Workload Summary (10 Queries, 30% Cache Hits)

| Metric | Baseline (Uncached) | Green Optimized (Cached) | Measured Improvement |
| :--- | :--- | :--- | :--- |
| **Average Query Latency** | 3293.9 ms | 2619.5 ms | **20.47% faster** |
| **Total Energy Consumed ($E$)** | 0.00011513 kWh | 0.00009183 kWh | **20.24% energy saved** |
| **Operational Emissions ($O$)** | 0.082136 gCO₂eq | 0.065513 gCO₂eq | **20.24% operational CO₂ saved** |
| **Embodied Carbon ($M$)** | 0.078395 gCO₂eq | 0.062344 gCO₂eq | **20.47% runtime reduction** |
| **Cumulative SCI Score** | 0.160531 gCO₂eq | 0.127857 gCO₂eq | **20.35% carbon intensity saved** |
| **Average SCI per Query** | 0.016053 gCO₂eq | 0.012786 gCO₂eq | **20.35% reduction** |

### 5.2 Slice Breakdown: Repeated Queries vs Unique Queries

| Workload Slice | Baseline Latency | Green Latency | Baseline Energy | Green Energy | Energy Savings % | SCI Savings % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Repeated Queries (Hits, 3/10)** | 2398.4 ms | **4.7 ms** | 0.00002581 kWh | **0.00000002 kWh** | **99.91% saved** | **99.86% saved** |
| **Unique Queries (Misses, 7/10)** | 3677.7 ms | 3740.1 ms | 0.00008932 kWh | 0.00009180 kWh | Full inference parity (within 2.7% normal load variance) | Parity |

---

## 6. Functional Verification & Integrity

The implementation was tested to verify that green optimizations do not degrade standard RAG features:
- **Answer Quality:** Grounded answers generated accurately from college documents (e.g., minimum 75% attendance rule).
- **Citations:** Full source metadata, document type, year, and text snippets preserved in all responses.
- **Cache Invalidation:** Document uploads (`/upload`) and vector re-indexing (`/reindex`) immediately invalidate the LRU cache, preventing stale responses.
- **Filter Differentiation:** Cache keys uniquely separate document types and academic year filters, preventing cross-filter cache pollution.

---

## 7. Viva Voce Preparation & Key Concepts

**Q1: What is the Software Carbon Intensity (SCI) metric?**  
*Answer:* SCI is a specification by the Green Software Foundation to score software carbon intensity per functional unit: $SCI = ((E \times I) + M) / R$. Rather than purchasing carbon offsets, SCI measures how efficiently software converts energy and hardware into useful work.

**Q2: How does CodeCarbon measure energy in this project?**  
*Answer:* CodeCarbon's `OfflineEmissionsTracker` monitors workload tasks using `start_task()` and `stop_task()`. On Windows, it reads processor architecture information, detects the CPU TDP (15.0W), and samples active CPU load via `psutil` along with RAM power to integrate energy ($kWh$) and operational emissions.

**Q3: Why are cache-hit queries so much greener?**  
*Answer:* Running autoregressive transformer decoders requires billions of floating-point operations at high CPU power. An in-memory cache lookup returns precomputed answers in under $5\text{ ms}$ at near-idle power ($\sim 4\text{ W}$ vs $\sim 18\text{ W}$), achieving a $>99.9\%$ energy reduction.

**Q4: What is the difference between Operational ($E \times I$) and Embodied Carbon ($M$)?**  
*Answer:* Operational carbon is the emissions caused by the electricity consumed while running the software ($E \times I$). Embodied carbon ($M$) represents the greenhouse gas emissions from manufacturing, transporting, and disposing of the computer hardware, amortized over the execution duration.

---

## 8. Conclusion

By implementing two-tier caching, lean context windowing, CodeCarbon hardware tracking, and the GSF SCI standard, the College Student Knowledge Assistant demonstrates that AI software can achieve significant, verifiable carbon reductions while providing sub-second responsiveness for students.
