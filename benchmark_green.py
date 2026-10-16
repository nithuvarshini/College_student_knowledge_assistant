"""
benchmark_green.py
Standalone Green Software Engineering Benchmark & Measurement Script.
Runs a representative suite of student questions in Baseline Mode vs Green Mode,
capturing real energy, latency, and Software Carbon Intensity (SCI) metrics.

Run with: python benchmark_green.py
"""

import os
import sys
import time
import json
import logging
from typing import List, Dict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GreenBenchmark")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "documents")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# Add project root to sys.path
sys.path.insert(0, BASE_DIR)

from src.rag_pipeline import RAGPipeline


SAMPLE_QUERIES = [
    "What is the minimum attendance required?",
    "When does the next semester start?",
    "What is the fine for returning a library book late?",
    "Am I eligible for placement with 1 backlog?",
    "What scholarships are available for 2nd year students?",
    "What are the prerequisites for Data Structures?",
    "How do I apply for a bonafide certificate?",
    "What is the minimum attendance required?",  # Repeated query
    "When does the next semester start?",        # Repeated query
    "What is the fine for returning a library book late?", # Repeated query
]


def run_benchmark():
    print("=" * 75)
    print("🌱 COLLEGE STUDENT KNOWLEDGE ASSISTANT — GREEN COMPUTING BENCHMARK")
    print("=" * 75)
    print(f"Initializing RAG Pipeline from {DOCS_DIR}...")

    rag = RAGPipeline(docs_dir=DOCS_DIR, chroma_dir=CHROMA_DIR, top_k=5)

    print(f"\nRunning test suite of {len(SAMPLE_QUERIES)} queries...")
    print("Simulating real student workload (including typical repeated inquiries)\n")

    # ── 1. BASELINE RUN (No caching, full model inference every time) ─────────
    print("[-] Executing Run 1: BASELINE MODE (Green Mode = OFF)...")
    base_results = []
    base_start = time.perf_counter()

    for idx, q in enumerate(SAMPLE_QUERIES, 1):
        res = rag.query(question=q, green_mode=False)
        gm = res["green_metrics"]
        base_results.append({
            "query_idx": idx,
            "question": q,
            "latency_ms": gm["duration_ms"],
            "energy_kwh": gm["energy_kwh"],
            "sci_score": gm["sci_score_g_co2_per_query"],
            "is_cache_hit": gm["is_cache_hit"],
        })
        print(f"   [{idx}/{len(SAMPLE_QUERIES)}] {q[:40]:<40} | {gm['duration_ms']:>6.1f} ms | {gm['sci_score_g_co2_per_query']:.6f} gCO2")

    base_total_time = time.perf_counter() - base_start

    # Reset tracker stats for clean green run
    rag.green_tracker.reset_stats()
    rag._invalidate_cache()

    # ── 2. GREEN OPTIMIZED RUN (Caching + Lean Context enabled) ───────────────
    print("\n[+] Executing Run 2: GREEN OPTIMIZED MODE (Green Mode = ON)...")
    green_results = []
    green_start = time.perf_counter()

    for idx, q in enumerate(SAMPLE_QUERIES, 1):
        res = rag.query(question=q, green_mode=True)
        gm = res["green_metrics"]
        green_results.append({
            "query_idx": idx,
            "question": q,
            "latency_ms": gm["duration_ms"],
            "energy_kwh": gm["energy_kwh"],
            "sci_score": gm["sci_score_g_co2_per_query"],
            "is_cache_hit": gm["is_cache_hit"],
        })
        hit_tag = "⚡ CACHE HIT" if gm["is_cache_hit"] else "⚙️ MISS"
        print(f"   [{idx}/{len(SAMPLE_QUERIES)}] {hit_tag:<12} | {q[:32]:<32} | {gm['duration_ms']:>6.1f} ms | {gm['sci_score_g_co2_per_query']:.6f} gCO2")

    green_total_time = time.perf_counter() - green_start

    # ── 3. METRICS AGGREGATION & COMPARISON ───────────────────────────────────
    base_total_energy = sum(r["energy_kwh"] for r in base_results)
    base_total_sci = sum(r["sci_score"] for r in base_results)
    base_avg_lat = sum(r["latency_ms"] for r in base_results) / len(base_results)

    green_total_energy = sum(r["energy_kwh"] for r in green_results)
    green_total_sci = sum(r["sci_score"] for r in green_results)
    green_avg_lat = sum(r["latency_ms"] for r in green_results) / len(green_results)
    green_cache_hits = sum(1 for r in green_results if r["is_cache_hit"])

    lat_reduction_pct = round(100 * (base_avg_lat - green_avg_lat) / base_avg_lat, 2)
    energy_reduction_pct = round(100 * (base_total_energy - green_total_energy) / base_total_energy, 2)
    sci_reduction_pct = round(100 * (base_total_sci - green_total_sci) / base_total_sci, 2)

    print("\n" + "=" * 75)
    print("📊 BENCHMARK RESULTS & SUSTAINABILITY IMPACT SUMMARY")
    print("=" * 75)
    print(f"{'Metric':<35} | {'Baseline (Uncached)':<18} | {'Green Optimized':<18} | {'Savings %':<10}")
    print("-" * 75)
    print(f"{'Average Query Latency (ms)':<35} | {base_avg_lat:<18.1f} | {green_avg_lat:<18.1f} | {lat_reduction_pct}%")
    print(f"{'Total Workload Duration (s)':<35} | {base_total_time:<18.2f} | {green_total_time:<18.2f} | {round(100*(base_total_time-green_total_time)/base_total_time, 2)}%")
    print(f"{'Total Energy Consumed (kWh)':<35} | {base_total_energy:<18.8f} | {green_total_energy:<18.8f} | {energy_reduction_pct}%")
    print(f"{'Total Cumulative SCI (gCO2eq)':<35} | {base_total_sci:<18.6f} | {green_total_sci:<18.6f} | {sci_reduction_pct}%")
    print(f"{'Average SCI per Query (gCO2eq/req)':<35} | {(base_total_sci/len(base_results)):<18.6f} | {(green_total_sci/len(green_results)):<18.6f} | {sci_reduction_pct}%")
    print(f"{'Cache Hit Ratio':<35} | {'0.0%':<18} | {f'{green_cache_hits}/{len(SAMPLE_QUERIES)} ({round(100*green_cache_hits/len(SAMPLE_QUERIES),1)}%)':<18} | —")
    print("=" * 75)

    # Export verified results to JSON
    report_data = {
        "benchmark_metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "queries_evaluated": len(SAMPLE_QUERIES),
            "cpu_tdp_watts": rag.green_tracker.cpu_tdp,
            "grid_intensity_g_kwh": rag.green_tracker.grid_intensity,
            "sci_standard": "GSF SCI = ((E * I) + M) / R",
        },
        "baseline_summary": {
            "average_latency_ms": round(base_avg_lat, 2),
            "total_duration_sec": round(base_total_time, 2),
            "total_energy_kwh": round(base_total_energy, 8),
            "total_sci_g_co2": round(base_total_sci, 6),
            "avg_sci_per_query_g": round(base_total_sci / len(base_results), 6),
        },
        "green_optimized_summary": {
            "average_latency_ms": round(green_avg_lat, 2),
            "total_duration_sec": round(green_total_time, 2),
            "total_energy_kwh": round(green_total_energy, 8),
            "total_sci_g_co2": round(green_total_sci, 6),
            "avg_sci_per_query_g": round(green_total_sci / len(green_results), 6),
            "cache_hits": green_cache_hits,
            "cache_hit_rate_pct": round(100 * green_cache_hits / len(SAMPLE_QUERIES), 1),
        },
        "percentage_improvements": {
            "latency_reduction_pct": lat_reduction_pct,
            "energy_reduction_pct": energy_reduction_pct,
            "sci_carbon_reduction_pct": sci_reduction_pct,
        },
        "query_details": {
            "baseline": base_results,
            "green_optimized": green_results,
        }
    }

    out_path = os.path.join(BASE_DIR, "green_benchmark_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n[✓] Verified results saved to: {out_path}\n")
    return report_data


if __name__ == "__main__":
    run_benchmark()
