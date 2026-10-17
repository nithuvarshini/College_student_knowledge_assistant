"""
src/green_tracker.py
Sustainability and Green Software Engineering measurement module.
Integrates CodeCarbon OfflineEmissionsTracker for empirical hardware energy tracking
and the Green Software Foundation (GSF) Software Carbon Intensity (SCI) standard:
SCI = ((E * I) + M) / R
"""

import atexit
import logging
import time
import uuid
from typing import Dict, Optional
try:
    from codecarbon import OfflineEmissionsTracker
    CODECARBON_AVAILABLE = True
except ImportError:
    OfflineEmissionsTracker = None
    CODECARBON_AVAILABLE = False

logger = logging.getLogger(__name__)

# Standard India national grid average ~713 gCO2eq/kWh in CodeCarbon
DEFAULT_COUNTRY_ISO = "IND"
DEFAULT_GRID_INTENSITY_G_PER_KWH = 713.0

# GSF Embodied Carbon (M) parameter:
# Typical laptop (Intel i5 / 8-16GB RAM): ~300 kg CO2eq embodied footprint over 4-year lifespan
# 300,000 g / (4 * 365 * 24 * 3600 s) ≈ 0.00238 gCO2eq per second of device runtime
EMBODIED_RATE_G_PER_SEC = 0.00238


class GreenTracker:
    """
    Manages CodeCarbon emissions tracking and computes the GSF Software
    Carbon Intensity (SCI) metric for individual queries and cumulative sessions.
    """

    def __init__(self, country_iso: str = DEFAULT_COUNTRY_ISO):
        self.country_iso = country_iso
        self._tracker: Optional[OfflineEmissionsTracker] = None
        self._tracker_active = False

        # Cumulative counters
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.cumulative_energy_kwh = 0.0
        self.cumulative_operational_co2_g = 0.0
        self.cumulative_embodied_co2_g = 0.0
        self.cumulative_sci_g_co2 = 0.0
        self.cumulative_energy_saved_kwh = 0.0
        self.cumulative_emissions_avoided_g_co2 = 0.0

        # Dynamic baseline reference (updated from actual uncached runs)
        self._last_uncached_energy_kwh = 0.0
        self._last_uncached_sci_g = 0.0

        self._init_tracker()
        atexit.register(self.shutdown)

    def _init_tracker(self):
        """Initializes and starts the underlying CodeCarbon OfflineEmissionsTracker."""
        try:
            self._tracker = OfflineEmissionsTracker(
                country_iso_code=self.country_iso,
                save_to_file=False,
                log_level="error",
                measure_power_secs=1,
            )
            self._tracker.start()
            self._tracker_active = True
            logger.info("CodeCarbon OfflineEmissionsTracker initialized and running.")
        except Exception as e:
            logger.warning("Could not initialize CodeCarbon tracker: %s. Using fallback.", e)
            self._tracker = None
            self._tracker_active = False

    def start_measurement(self, task_name: Optional[str] = None) -> str:
        """Begins tracking a workload task."""
        t_id = task_name or f"rag_task_{uuid.uuid4().hex[:8]}"
        if self._tracker and self._tracker_active:
            try:
                self._tracker.start_task(t_id)
            except Exception as e:
                logger.debug("CodeCarbon start_task error: %s", e)
        return t_id

    def stop_measurement(
        self,
        task_name: str,
        is_cache_hit: bool,
        fallback_duration_sec: float = 0.001,
    ) -> Dict:
        """
        Stops tracking the workload task and computes the GSF SCI metric:
            SCI = ((E * I) + M) / R
        where:
            E = Measured energy in kWh (from CodeCarbon)
            I = Grid carbon intensity (gCO2eq/kWh)
            M = Embodied carbon in gCO2eq (amortized hardware model)
            R = Functional unit (1 query)
        """
        self.total_queries += 1

        measured_energy_kwh = 0.0
        operational_co2_g = 0.0
        duration_sec = fallback_duration_sec
        cpu_power_w = 0.0
        ram_power_w = 0.0

        if self._tracker and self._tracker_active:
            try:
                emissions_data = self._tracker.stop_task(task_name)
                if emissions_data:
                    measured_energy_kwh = float(emissions_data.energy_consumed or 0.0)
                    # CodeCarbon reports emissions in kg CO2eq -> convert to grams
                    operational_co2_g = float((emissions_data.emissions or 0.0) * 1000.0)
                    duration_sec = float(emissions_data.duration or fallback_duration_sec)
                    cpu_power_w = float(emissions_data.cpu_power or 0.0)
                    ram_power_w = float(emissions_data.ram_power or 0.0)
            except Exception as e:
                logger.warning("Error stopping CodeCarbon task '%s': %s", task_name, e)

        # Ensure sensible lower bounds for duration
        duration_sec = max(duration_sec, 0.0001)

        # Fallback if tracker returned zero energy on very fast operations
        if measured_energy_kwh <= 0.0:
            est_power = (cpu_power_w or 4.0) + (ram_power_w or 2.0)
            measured_energy_kwh = (est_power * duration_sec) / 3600000.0
            operational_co2_g = measured_energy_kwh * DEFAULT_GRID_INTENSITY_G_PER_KWH

        # Embodied carbon (M) per GSF formula (amortized hardware lifecycle)
        embodied_co2_g = EMBODIED_RATE_G_PER_SEC * duration_sec

        # Total SCI score (R = 1 query)
        sci_score = operational_co2_g + embodied_co2_g

        # Accumulate metrics
        if is_cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self._last_uncached_energy_kwh = measured_energy_kwh
            self._last_uncached_sci_g = sci_score

        self.cumulative_energy_kwh += measured_energy_kwh
        self.cumulative_operational_co2_g += operational_co2_g
        self.cumulative_embodied_co2_g += embodied_co2_g
        self.cumulative_sci_g_co2 += sci_score

        # Calculate savings if serving from cache compared to the latest un-cached query
        energy_saved_kwh = 0.0
        emissions_saved_g = 0.0
        if is_cache_hit and self._last_uncached_energy_kwh > 0.0:
            energy_saved_kwh = max(0.0, self._last_uncached_energy_kwh - measured_energy_kwh)
            emissions_saved_g = max(0.0, self._last_uncached_sci_g - sci_score)
            self.cumulative_energy_saved_kwh += energy_saved_kwh
            self.cumulative_emissions_avoided_g_co2 += emissions_saved_g

        return {
            "is_cache_hit": is_cache_hit,
            "duration_ms": round(duration_sec * 1000.0, 2),
            "measured_energy_kwh": float(f"{measured_energy_kwh:.10f}"),
            "estimated_operational_co2_g": float(f"{operational_co2_g:.8f}"),
            "assumed_embodied_co2_g": float(f"{embodied_co2_g:.8f}"),
            "sci_score_g_co2_per_query": float(f"{sci_score:.8f}"),
            "power_telemetry": {
                "cpu_power_watts": round(cpu_power_w, 2),
                "ram_power_watts": round(ram_power_w, 2),
            },
            "savings_vs_last_uncached": {
                "energy_saved_kwh": float(f"{energy_saved_kwh:.10f}"),
                "emissions_avoided_g": float(f"{emissions_saved_g:.8f}"),
            },
            "methodology": {
                "energy_measurement": "CodeCarbon OfflineEmissionsTracker (actual workload task tracking)",
                "operational_emissions": f"CodeCarbon regional grid intensity for {self.country_iso} (~{DEFAULT_GRID_INTENSITY_G_PER_KWH} gCO2eq/kWh)",
                "embodied_carbon_model": f"GSF amortized client hardware baseline ({EMBODIED_RATE_G_PER_SEC} gCO2eq/s based on 300kg CO2eq over 4-year lifespan)",
                "sci_standard": "GSF SCI = ((E * I) + M) / R (R = 1 query)",
            },
            "limitations": [
                "CPU power on Windows is estimated by CodeCarbon using CPU TDP and utilization load (Intel RAPL/EMI interface is unavailable without admin/hypervisor support).",
                "Embodied carbon (M) is an amortized model assumption per GSF specifications and cannot be measured dynamically by physical sensors.",
                "Network transmission energy and upstream datacenter PUE are excluded from this local endpoint boundary.",
            ],
        }

    def get_summary(self) -> Dict:
        """Returns cumulative sustainability KPIs for dashboards and reports."""
        hit_rate = (
            round(100.0 * self.cache_hits / self.total_queries, 2)
            if self.total_queries > 0
            else 0.0
        )
        avg_sci = (
            round(self.cumulative_sci_g_co2 / self.total_queries, 8)
            if self.total_queries > 0
            else 0.0
        )

        return {
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate_pct": hit_rate,
            "cumulative_measured_energy_kwh": float(f"{self.cumulative_energy_kwh:.10f}"),
            "cumulative_operational_co2_g": float(f"{self.cumulative_operational_co2_g:.8f}"),
            "cumulative_embodied_co2_g": float(f"{self.cumulative_embodied_co2_g:.8f}"),
            "cumulative_sci_g_co2": float(f"{self.cumulative_sci_g_co2:.8f}"),
            "average_sci_g_co2_per_query": avg_sci,
            "cumulative_energy_saved_kwh": float(f"{self.cumulative_energy_saved_kwh:.10f}"),
            "cumulative_emissions_avoided_g_co2": float(f"{self.cumulative_emissions_avoided_g_co2:.8f}"),
            "measurement_backend": "CodeCarbon OfflineEmissionsTracker",
            "country_iso": self.country_iso,
        }

    def reset_stats(self):
        """Resets cumulative counters."""
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.cumulative_energy_kwh = 0.0
        self.cumulative_operational_co2_g = 0.0
        self.cumulative_embodied_co2_g = 0.0
        self.cumulative_sci_g_co2 = 0.0
        self.cumulative_energy_saved_kwh = 0.0
        self.cumulative_emissions_avoided_g_co2 = 0.0
        self._last_uncached_energy_kwh = 0.0
        self._last_uncached_sci_g = 0.0

    def shutdown(self):
        """Safely stops the CodeCarbon tracker on program exit."""
        if self._tracker and self._tracker_active:
            try:
                self._tracker.stop()
                self._tracker_active = False
                logger.info("CodeCarbon tracker stopped.")
            except Exception as e:
                logger.debug("CodeCarbon shutdown exception: %s", e)
