"""
benchmark_green.py
Fair, scientific Green Software Engineering benchmark suite.
Compares Baseline (Uncached) vs Green Optimized (Two-tier Caching + Lean Processing)
using identical queries, warm-up runs, multi-trial averaging, and explicit
cache-hit vs cache-miss breakdown.
Captures actual CodeCarbon energy measurements and calculates GSF SCI metrics.

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GreenBenchmark")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "documents")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

sys.path.insert(0, BASE_DIR)

from src.rag_pipeline import RAGPipeline
from src.green_tracker import DEFAULT_GRID_INTENSITY_G_PER_KWH, EMBODIED_RATE_G_PER_SEC

# Workload design:
# Queries 1-5: Unique questions (initial queries)
# Queries 6-8: Repeated questions (tests cache-hit behavior)
# Queries 9-10: Additional unique questions (tests ongoing cache-miss behavior)
BENCHMARK_QUERIES = [
    # Initial unique queries (Miss)
    "What is the minimum attendance required?",
    "When does the next semester start?",
    "What is the fine for returning a library book late?",
    "Am I eligible for placement with 1 backlog?",
    "What scholarships are available for 2nd year students?",
    # Repeated queries (Hit in green mode, Miss in baseline)
    "What is the minimum attendance required?",
    "When does the next semester start?",
    "What is the fine for returning a library book late?",
    # Additional unique queries (Miss)
    "What are the prerequisites for Data Structures?",
    "How do I apply for a bonafide certificate?",
]

TRIALS_PER_MODE = 2


def run_benchmark():
    print("=" * 80)
    print("🌱 COLLEGE STUDENT KNOWLEDGE ASSISTANT — SCIENTIFIC GREEN BENCHMARK")
    print("=" * 80)
    print(f"Initializing RAG Pipeline from: {DOCS_DIR}")
    rag = RAGPipeline(docs_dir=DOCS_DIR, chroma_dir=CHROMA_DIR, top_k=5)

    # ── STEP 1: WARM-UP RUN (Eliminate cold-start model loading bias) ─────────
    print("\n[0/3] Warming up model weights, PyTorch graph, and vector store...")
    _ = rag.query("Warmup query: attendance criteria?", green_mode=False)
    _ = rag.query("Warmup query: calendar dates?", green_mode=False)
    rag._invalidate_cache()
    rag.green_tracker.reset_stats()
    print("      Warm-up complete. Both modes will now be measured on equal terms.")

    # ── STEP 2: BASELINE RUN (Green Mode = OFF, 2 trials) ────────────────────
    print(f"\n[1/3] Executing BASELINE MODE ({TRIALS_PER_MODE} trials, Caching = OFF)...")
    baseline_query_records: List[List[Dict]] = []

    for trial in range(1, TRIALS_PER_MODE + 1):
        print(f"   --- Starting Baseline Trial {trial}/{TRIALS_PER_MODE} ---")
        trial_records = []
        for idx, q in enumerate(BENCHMARK_QUERIES, 1):
            res = rag.query(question=q, green_mode=False)
            gm = res["green_metrics"]
            trial_records.append({
                "query_idx": idx,
                "question": q,
                "duration_ms": gm["duration_ms"],
                "energy_kwh": gm["energy_kwh"],
                "is_directly_measured": gm.get("energy_is_directly_measured", False),
                "measurement_type": gm.get("energy_measurement_type", "unknown"),
                "operational_co2_g": gm["operational_co2_g"],
                "embodied_co2_g": gm["embodied_co2_g"],
                "sci_score": gm["sci_score_g_co2_per_query"],
                "is_cache_hit": gm["is_cache_hit"],
            })
            print(f"      [{idx:02d}/{len(BENCHMARK_QUERIES)}] {q[:36]:<36} | {gm['duration_ms']:>6.1f} ms | {gm['sci_score_g_co2_per_query']:.6f} gCO2")
        baseline_query_records.append(trial_records)

    # Compute averaged baseline metrics per query
    averaged_baseline = []
    for q_idx in range(len(BENCHMARK_QUERIES)):
        avg_dur = sum(baseline_query_records[t][q_idx]["duration_ms"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_energy = sum(baseline_query_records[t][q_idx]["energy_kwh"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_op = sum(baseline_query_records[t][q_idx]["operational_co2_g"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_emb = sum(baseline_query_records[t][q_idx]["embodied_co2_g"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_sci = sum(baseline_query_records[t][q_idx]["sci_score"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        is_measured = baseline_query_records[0][q_idx]["is_directly_measured"]
        meas_type = baseline_query_records[0][q_idx]["measurement_type"]
        averaged_baseline.append({
            "query_idx": q_idx + 1,
            "question": BENCHMARK_QUERIES[q_idx],
            "duration_ms": round(avg_dur, 2),
            "energy_kwh": float(f"{avg_energy:.10f}"),
            "directly_measured_energy_kwh": float(f"{avg_energy:.10f}") if is_measured else None,
            "estimated_energy_kwh": float(f"{avg_energy:.10f}") if not is_measured else None,
            "is_directly_measured": is_measured,
            "measurement_type": meas_type,
            "energy_status": "directly_measured" if is_measured else "modeled_estimate",
            "energy_status_description": "Directly tracked via CodeCarbon" if is_measured else "Modeled estimate (sensor fallback)",
            "operational_co2_g": float(f"{avg_op:.8f}"),
            "embodied_co2_g": float(f"{avg_emb:.8f}"),
            "sci_score": float(f"{avg_sci:.8f}"),
            "is_cache_hit": False,
        })

    # Reset cache and counters for clean Green mode measurement
    rag._invalidate_cache()
    rag.green_tracker.reset_stats()

    # ── STEP 3: GREEN OPTIMIZED RUN (Green Mode = ON, 2 trials) ──────────────
    print(f"\n[2/3] Executing GREEN OPTIMIZED MODE ({TRIALS_PER_MODE} trials, Caching = ON)...")
    green_query_records: List[List[Dict]] = []

    for trial in range(1, TRIALS_PER_MODE + 1):
        print(f"   --- Starting Green Trial {trial}/{TRIALS_PER_MODE} ---")
        rag._invalidate_cache()  # Clean cache so both trials follow identical: 5 misses -> 3 hits -> 2 misses
        trial_records = []
        for idx, q in enumerate(BENCHMARK_QUERIES, 1):
            res = rag.query(question=q, green_mode=True)
            gm = res["green_metrics"]
            trial_records.append({
                "query_idx": idx,
                "question": q,
                "duration_ms": gm["duration_ms"],
                "energy_kwh": gm["energy_kwh"],
                "is_directly_measured": gm.get("energy_is_directly_measured", False),
                "measurement_type": gm.get("energy_measurement_type", "unknown"),
                "operational_co2_g": gm["operational_co2_g"],
                "embodied_co2_g": gm["embodied_co2_g"],
                "sci_score": gm["sci_score_g_co2_per_query"],
                "is_cache_hit": gm["is_cache_hit"],
            })
            status = "⚡ HIT " if gm["is_cache_hit"] else "⚙️ MISS"
            print(f"      [{idx:02d}/{len(BENCHMARK_QUERIES)}] {status} | {q[:32]:<32} | {gm['duration_ms']:>6.1f} ms | {gm['sci_score_g_co2_per_query']:.6f} gCO2")
        green_query_records.append(trial_records)

    # Compute averaged green metrics per query
    averaged_green = []
    for q_idx in range(len(BENCHMARK_QUERIES)):
        avg_dur = sum(green_query_records[t][q_idx]["duration_ms"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_energy = sum(green_query_records[t][q_idx]["energy_kwh"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_op = sum(green_query_records[t][q_idx]["operational_co2_g"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_emb = sum(green_query_records[t][q_idx]["embodied_co2_g"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        avg_sci = sum(green_query_records[t][q_idx]["sci_score"] for t in range(TRIALS_PER_MODE)) / TRIALS_PER_MODE
        is_hit = green_query_records[0][q_idx]["is_cache_hit"]
        is_measured = green_query_records[0][q_idx]["is_directly_measured"]
        meas_type = green_query_records[0][q_idx]["measurement_type"]
        averaged_green.append({
            "query_idx": q_idx + 1,
            "question": BENCHMARK_QUERIES[q_idx],
            "duration_ms": round(avg_dur, 2),
            "energy_kwh": float(f"{avg_energy:.10f}"),
            "directly_measured_energy_kwh": float(f"{avg_energy:.10f}") if is_measured else None,
            "estimated_energy_kwh": float(f"{avg_energy:.10f}") if not is_measured else None,
            "is_directly_measured": is_measured,
            "measurement_type": meas_type,
            "energy_status": "directly_measured" if is_measured else "modeled_estimate",
            "energy_status_description": "Directly tracked via CodeCarbon" if is_measured else ("Modeled estimate (sub-ms cache hit)" if is_hit else "Modeled estimate (sensor fallback)"),
            "operational_co2_g": float(f"{avg_op:.8f}"),
            "embodied_co2_g": float(f"{avg_emb:.8f}"),
            "sci_score": float(f"{avg_sci:.8f}"),
            "is_cache_hit": is_hit,
        })

    # ── STEP 4: DETAILED STATISTICAL ANALYSIS & SEPARATION ───────────────────
    # A. Overall Workload
    base_tot_energy = sum(r["energy_kwh"] for r in averaged_baseline)
    base_tot_sci = sum(r["sci_score"] for r in averaged_baseline)
    base_avg_lat = sum(r["duration_ms"] for r in averaged_baseline) / len(averaged_baseline)

    green_tot_energy = sum(r["energy_kwh"] for r in averaged_green)
    green_tot_sci = sum(r["sci_score"] for r in averaged_green)
    green_avg_lat = sum(r["duration_ms"] for r in averaged_green) / len(averaged_green)

    overall_lat_saved_pct = round(100 * (base_avg_lat - green_avg_lat) / base_avg_lat, 2)
    overall_energy_saved_pct = round(100 * (base_tot_energy - green_tot_energy) / base_tot_energy, 2)
    overall_sci_saved_pct = round(100 * (base_tot_sci - green_tot_sci) / base_tot_sci, 2)

    # B. Cache Hits (Repeated Queries, indices 5, 6, 7 -> items 6, 7, 8)
    hit_indices = [i for i, r in enumerate(averaged_green) if r["is_cache_hit"]]
    if hit_indices:
        hit_base_lat = sum(averaged_baseline[i]["duration_ms"] for i in hit_indices) / len(hit_indices)
        hit_green_lat = sum(averaged_green[i]["duration_ms"] for i in hit_indices) / len(hit_indices)
        hit_base_energy = sum(averaged_baseline[i]["energy_kwh"] for i in hit_indices)
        hit_green_energy = sum(averaged_green[i]["energy_kwh"] for i in hit_indices)
        hit_base_sci = sum(averaged_baseline[i]["sci_score"] for i in hit_indices)
        hit_green_sci = sum(averaged_green[i]["sci_score"] for i in hit_indices)

        hit_lat_pct = round(100 * (hit_base_lat - hit_green_lat) / hit_base_lat, 2)
        hit_energy_pct = round(100 * (hit_base_energy - hit_green_energy) / max(hit_base_energy, 1e-12), 2)
        hit_sci_pct = round(100 * (hit_base_sci - hit_green_sci) / max(hit_base_sci, 1e-12), 2)
    else:
        hit_base_lat = hit_green_lat = hit_lat_pct = 0.0
        hit_base_energy = hit_green_energy = hit_energy_pct = 0.0
        hit_base_sci = hit_green_sci = hit_sci_pct = 0.0

    # C. Cache Misses (Unique Queries)
    miss_indices = [i for i, r in enumerate(averaged_green) if not r["is_cache_hit"]]
    if miss_indices:
        miss_base_lat = sum(averaged_baseline[i]["duration_ms"] for i in miss_indices) / len(miss_indices)
        miss_green_lat = sum(averaged_green[i]["duration_ms"] for i in miss_indices) / len(miss_indices)
        miss_base_energy = sum(averaged_baseline[i]["energy_kwh"] for i in miss_indices)
        miss_green_energy = sum(averaged_green[i]["energy_kwh"] for i in miss_indices)
        miss_base_sci = sum(averaged_baseline[i]["sci_score"] for i in miss_indices)
        miss_green_sci = sum(averaged_green[i]["sci_score"] for i in miss_indices)
    else:
        miss_base_lat = miss_green_lat = 0.0
        miss_base_energy = miss_green_energy = 0.0
        miss_base_sci = miss_green_sci = 0.0

    # ── STEP 5: PRINT SUMMARY TABLE ──────────────────────────────────────────
    print("\n" + "=" * 80)
    print("📊 FAIR BENCHMARK SUMMARY (AVERAGED OVER 2 TRIALS WITH WARM-UP)")
    print("=" * 80)
    print(f"{'Workload Slice / Metric':<35} | {'Baseline (Uncached)':<18} | {'Green Optimized':<18} | {'Improvement':<12}")
    print("-" * 80)
    print(f"[A] OVERALL WORKLOAD (10 Queries)")
    print(f"    Avg Latency per Query (ms)      | {base_avg_lat:<18.1f} | {green_avg_lat:<18.1f} | {overall_lat_saved_pct}% faster")
    print(f"    Total Energy Consumed (kWh)     | {base_tot_energy:<18.8f} | {green_tot_energy:<18.8f} | {overall_energy_saved_pct}% saved")
    print(f"    Cumulative SCI (gCO2eq)         | {base_tot_sci:<18.6f} | {green_tot_sci:<18.6f} | {overall_sci_saved_pct}% saved")
    print(f"    Avg SCI per Query (gCO2eq/req)  | {(base_tot_sci/len(averaged_baseline)):<18.6f} | {(green_tot_sci/len(averaged_green)):<18.6f} | {overall_sci_saved_pct}% saved")
    print("-" * 80)
    print(f"[B] REPEATED QUERIES (Cache Hits: {len(hit_indices)}/{len(BENCHMARK_QUERIES)})")
    print(f"    Avg Latency per Hit (ms)        | {hit_base_lat:<18.1f} | {hit_green_lat:<18.1f} | {hit_lat_pct}% faster")
    print(f"    Energy on Repeated Queries(kWh) | {hit_base_energy:<18.8f} | {hit_green_energy:<18.8f} | {hit_energy_pct}% saved")
    print(f"    SCI on Repeated Queries (gCO2)  | {hit_base_sci:<18.6f} | {hit_green_sci:<18.6f} | {hit_sci_pct}% saved")
    print("-" * 80)
    print(f"[C] UNIQUE QUERIES (Cache Misses: {len(miss_indices)}/{len(BENCHMARK_QUERIES)})")
    print(f"    Avg Latency per Miss (ms)       | {miss_base_lat:<18.1f} | {miss_green_lat:<18.1f} | Lean context")
    print(f"    Energy on Unique Queries (kWh)  | {miss_base_energy:<18.8f} | {miss_green_energy:<18.8f} | Full inference")
    print("=" * 80)

    # ── STEP 6: EXPORT ACTUAL EMPIRICAL RESULTS ──────────────────────────────
    results_payload = {
        "benchmark_metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "measurement_tool": "CodeCarbon OfflineEmissionsTracker (actual task tracking)",
            "trials_per_mode": TRIALS_PER_MODE,
            "warmup_queries_executed": 2,
            "queries_per_trial": len(BENCHMARK_QUERIES),
            "sci_standard": "GSF SCI = ((E * I) + M) / R",
            "country_iso": rag.green_tracker.country_iso,
            "assumptions_and_models": {
                "grid_intensity_g_per_kwh": DEFAULT_GRID_INTENSITY_G_PER_KWH,
                "embodied_carbon_rate_g_per_sec": EMBODIED_RATE_G_PER_SEC,
                "embodied_carbon_basis": "GSF amortized client device model (300 kg CO2eq / 4-yr lifespan)",
                "functional_unit_R": "1 query served",
            },
            "energy_reporting_transparency": {
                "direct_measurements": "Uncached queries with neural model inference are directly tracked by CodeCarbon per task.",
                "modeled_estimates": "Sub-millisecond cache hits fall below physical hardware sensor polling intervals and are explicitly reported as modeled estimates using measured baseline idle power (~5.5W)."
            },
            "limitations": [
                "CPU energy on Windows is estimated by CodeCarbon using CPU TDP and utilization load (Intel RAPL/EMI interface is restricted on standard Windows).",
                "Embodied carbon (M) is an amortized model assumption per GSF specifications and cannot be measured dynamically by physical sensors.",
                "Network transmission energy and upstream datacenter PUE are excluded from this local endpoint boundary.",
            ]
        },
        "overall_workload_comparison": {
            "baseline": {
                "average_latency_ms": round(base_avg_lat, 2),
                "total_energy_kwh": float(f"{base_tot_energy:.10f}"),
                "total_operational_co2_g": float(f"{sum(r['operational_co2_g'] for r in averaged_baseline):.8f}"),
                "total_embodied_co2_g": float(f"{sum(r['embodied_co2_g'] for r in averaged_baseline):.8f}"),
                "total_sci_g_co2": float(f"{base_tot_sci:.8f}"),
                "avg_sci_per_query_g": float(f"{(base_tot_sci/len(averaged_baseline)):.8f}"),
            },
            "green_optimized": {
                "average_latency_ms": round(green_avg_lat, 2),
                "total_energy_kwh": float(f"{green_tot_energy:.10f}"),
                "total_operational_co2_g": float(f"{sum(r['operational_co2_g'] for r in averaged_green):.8f}"),
                "total_embodied_co2_g": float(f"{sum(r['embodied_co2_g'] for r in averaged_green):.8f}"),
                "total_sci_g_co2": float(f"{green_tot_sci:.8f}"),
                "avg_sci_per_query_g": float(f"{(green_tot_sci/len(averaged_green)):.8f}"),
                "cache_hit_count": len(hit_indices),
                "cache_hit_rate_pct": round(100 * len(hit_indices) / len(BENCHMARK_QUERIES), 1),
            },
            "improvements": {
                "latency_reduction_pct": overall_lat_saved_pct,
                "energy_reduction_pct": overall_energy_saved_pct,
                "sci_carbon_reduction_pct": overall_sci_saved_pct,
            }
        },
        "cache_hits_slice": {
            "hit_count": len(hit_indices),
            "baseline_avg_latency_ms": round(hit_base_lat, 2),
            "green_avg_latency_ms": round(hit_green_lat, 2),
            "latency_reduction_pct": hit_lat_pct,
            "baseline_total_energy_kwh": float(f"{hit_base_energy:.10f}"),
            "green_total_energy_kwh": float(f"{hit_green_energy:.10f}"),
            "energy_reduction_pct": hit_energy_pct,
            "baseline_total_sci_g": float(f"{hit_base_sci:.8f}"),
            "green_total_sci_g": float(f"{hit_green_sci:.8f}"),
            "sci_reduction_pct": hit_sci_pct,
        },
        "cache_misses_slice": {
            "miss_count": len(miss_indices),
            "baseline_avg_latency_ms": round(miss_base_lat, 2),
            "green_avg_latency_ms": round(miss_green_lat, 2),
            "baseline_total_energy_kwh": float(f"{miss_base_energy:.10f}"),
            "green_total_energy_kwh": float(f"{miss_green_energy:.10f}"),
            "baseline_total_sci_g": float(f"{miss_base_sci:.8f}"),
            "green_total_sci_g": float(f"{miss_green_sci:.8f}"),
        },
        "query_breakdown": {
            "baseline_queries": averaged_baseline,
            "green_queries": averaged_green,
        }
    }

    out_file = os.path.join(BASE_DIR, "green_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print(f"\n[✓] Real benchmark results saved to: {out_file}\n")
    return results_payload


if __name__ == "__main__":
    run_benchmark()
