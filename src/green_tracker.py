"""
src/green_tracker.py
Sustainability and Green Software Engineering measurement module.
Integrates CodeCarbon principles and the Green Software Foundation (GSF)
Software Carbon Intensity (SCI) specification: SCI = ((E * I) + M) / R
"""

import os
import time
import psutil
from typing import Dict, Optional

# Grid Carbon Intensity (I) in gCO2eq/kWh
# Standard India national grid average ~710 gCO2eq/kWh (Central Electricity Authority)
# Global grid average ~475 gCO2eq/kWh
DEFAULT_GRID_INTENSITY_G_PER_KWH = 710.0

# Base hardware assumptions (GSF Embodied Carbon - M)
# Typical laptop (Intel i5 / 16GB RAM): ~300 kg CO2eq embodied footprint over 4-year lifespan
# 300 kg / (4 * 365 * 24 * 3600 s) ≈ 0.00238 gCO2eq per second of device runtime
EMBODIED_RATE_G_PER_SEC = 0.00238

# Hardware TDP baseline in Watts
DEFAULT_CPU_TDP_WATTS = 15.0
DEFAULT_RAM_POWER_WATTS = 2.5
IDLE_SYSTEM_POWER_WATTS = 3.5


class GreenTracker:
    """
    Measures and estimates operational energy, carbon footprint, and SCI score
    for individual queries and cumulative pipeline operations.
    """

    def __init__(self, grid_intensity: float = DEFAULT_GRID_INTENSITY_G_PER_KWH):
        self.grid_intensity = grid_intensity  # I (gCO2eq / kWh)
        self.cpu_tdp = self._detect_cpu_tdp()
        self.ram_power = DEFAULT_RAM_POWER_WATTS
        self.idle_power = IDLE_SYSTEM_POWER_WATTS

        # Cumulative counters
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_energy_kwh = 0.0
        self.total_emissions_g = 0.0
        self.total_energy_saved_kwh = 0.0
        self.total_emissions_saved_g = 0.0

        # Calibration baseline for un-cached query (used to compute savings)
        self._last_uncached_energy_kwh = 0.000008  # Default estimate until first un-cached query runs

    def _detect_cpu_tdp(self) -> float:
        """Attempts to read CPU TDP using CodeCarbon or falls back to typical 15W."""
        try:
            from codecarbon.core.cpu import TDP
            tdp_val = TDP().tdp
            if tdp_val and tdp_val > 0:
                return float(tdp_val)
        except Exception:
            pass
        return DEFAULT_CPU_TDP_WATTS

    def record_query(
        self,
        duration_sec: float,
        is_cache_hit: bool,
        cpu_utilization_pct: Optional[float] = None,
    ) -> Dict:
        """
        Calculates SCI metric for a single query (R = 1 functional unit):
            SCI = ((E * I) + M) / R
        where:
            E = Energy in kWh = (Power in Watts * duration_sec) / (1000 * 3600)
            I = Carbon Intensity in gCO2eq/kWh
            M = Embodied Carbon in gCO2eq = EMBODIED_RATE_G_PER_SEC * duration_sec
            R = 1 query
        """
        self.total_queries += 1

        if cpu_utilization_pct is None:
            try:
                cpu_utilization_pct = psutil.cpu_percent(interval=None)
            except Exception:
                cpu_utilization_pct = 70.0 if not is_cache_hit else 5.0

        if is_cache_hit:
            self.cache_hits += 1
            # Near-instant memory lookup: low power, fraction of a millisecond
            active_power_watts = self.idle_power + (self.cpu_tdp * 0.08)
        else:
            self.cache_misses += 1
            # Active embedding + generation load
            load_factor = max(0.2, min(1.0, (cpu_utilization_pct or 75.0) / 100.0))
            active_power_watts = self.idle_power + (self.cpu_tdp * load_factor) + self.ram_power

        # Energy consumed in kWh: E = (Watts * seconds) / (1000 * 3600)
        energy_kwh = (active_power_watts * duration_sec) / 3600000.0

        # Operational emissions: O = E * I (in gCO2eq)
        operational_g_co2 = energy_kwh * self.grid_intensity

        # Embodied emissions: M (in gCO2eq)
        embodied_g_co2 = EMBODIED_RATE_G_PER_SEC * duration_sec

        # SCI metric per functional unit (1 query): SCI = (E * I + M) / 1
        sci_score = operational_g_co2 + embodied_g_co2

        # Accumulate totals
        self.total_energy_kwh += energy_kwh
        self.total_emissions_g += sci_score

        # Track savings
        if not is_cache_hit:
            self._last_uncached_energy_kwh = max(energy_kwh, 0.000002)
            energy_saved_kwh = 0.0
            emissions_saved_g = 0.0
        else:
            # Savings compared to running full pipeline
            energy_saved_kwh = max(0.0, self._last_uncached_energy_kwh - energy_kwh)
            emissions_saved_g = (energy_saved_kwh * self.grid_intensity) + max(0.0, (EMBODIED_RATE_G_PER_SEC * 1.0) - embodied_g_co2)
            self.total_energy_saved_kwh += energy_saved_kwh
            self.total_emissions_saved_g += emissions_saved_g

        return {
            "is_cache_hit": is_cache_hit,
            "duration_ms": round(duration_sec * 1000.0, 2),
            "estimated_power_watts": round(active_power_watts, 2),
            "energy_kwh": float(f"{energy_kwh:.8f}"),
            "operational_co2_g": float(f"{operational_g_co2:.6f}"),
            "embodied_co2_g": float(f"{embodied_g_co2:.6f}"),
            "sci_score_g_co2_per_query": float(f"{sci_score:.6f}"),
            "energy_saved_vs_baseline_kwh": float(f"{energy_saved_kwh:.8f}"),
            "emissions_saved_g": float(f"{emissions_saved_g:.6f}"),
            "grid_intensity_g_per_kwh": self.grid_intensity,
            "sci_formula": "SCI = ((E * I) + M) / R [GSF Standard]",
        }

    def get_summary(self) -> Dict:
        """Returns cumulative sustainability KPIs for dashboard and reporting."""
        hit_rate = (
            round(100.0 * self.cache_hits / self.total_queries, 2)
            if self.total_queries > 0
            else 0.0
        )
        avg_sci = (
            round(self.total_emissions_g / self.total_queries, 6)
            if self.total_queries > 0
            else 0.0
        )

        return {
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate_pct": hit_rate,
            "cumulative_energy_kwh": float(f"{self.total_energy_kwh:.8f}"),
            "cumulative_emissions_g_co2": float(f"{self.total_emissions_g:.6f}"),
            "cumulative_energy_saved_kwh": float(f"{self.total_energy_saved_kwh:.8f}"),
            "cumulative_emissions_avoided_g_co2": float(f"{self.total_emissions_saved_g:.6f}"),
            "average_sci_g_co2_per_query": avg_sci,
            "hardware_specs": {
                "cpu_tdp_watts": self.cpu_tdp,
                "idle_power_watts": self.idle_power,
                "grid_intensity_g_kwh": self.grid_intensity,
            },
        }

    def reset_stats(self):
        """Resets cumulative counters."""
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_energy_kwh = 0.0
        self.total_emissions_g = 0.0
        self.total_energy_saved_kwh = 0.0
        self.total_emissions_saved_g = 0.0
