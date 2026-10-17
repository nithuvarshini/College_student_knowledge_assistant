"""
src/green_tracker.py
Sustainability and Green Software Engineering measurement module.
Integrates CodeCarbon OfflineEmissionsTracker for workload energy tracking
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

# Standard India national grid intensity in CodeCarbon (~713.0 gCO2eq/kWh)
DEFAULT_COUNTRY_ISO = "IND"
DEFAULT_GRID_INTENSITY_G_PER_KWH = 713.0

# GSF Embodied Carbon (M) parameter:
# Typical laptop (Intel i5 / 8-16GB RAM): ~300 kg CO2eq embodied footprint over 4-year lifespan
# 300,000 g / (4 * 365 * 24 * 3600 s) ≈ 0.00238 gCO2eq per second of device runtime
EMBODIED_RATE_G_PER_SEC = 0.00238

# Baseline idle system power for sub-millisecond estimation
IDLE_SYSTEM_POWER_WATTS = 5.5


class GreenTracker:
    """
    Manages CodeCarbon emissions tracking and computes the GSF Software
    Carbon Intensity (SCI) metric for individual queries and cumulative sessions.
    Clearly distinguishes directly measured hardware energy from modeled estimates.
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
        self.cumulative_directly_measured_kwh = 0.0
        self.cumulative_modeled_energy_kwh = 0.0
        self.cumulative_operational_co2_g = 0.0
        self.cumulative_embodied_co2_g = 0.0
        self.cumulative_sci_g_co2 = 0.0
        self.cumulative_energy_saved_kwh = 0.0
        self.cumulative_emissions_avoided_g_co2 = 0.0

        # Reference for calculating cache-hit savings against previous uncached query
        self._last_uncached_energy_kwh = 0.0
        self._last_uncached_sci_g = 0.0

        self._init_tracker()
        atexit.register(self.shutdown)

    def _init_tracker(self):
        """Initializes and starts the underlying CodeCarbon OfflineEmissionsTracker."""
        if not CODECARBON_AVAILABLE:
            logger.warning(
                "CodeCarbon is not installed in the active environment. "
                "Hardware tracking will use fallback modeling."
            )
            return

        try:
            self._tracker = OfflineEmissionsTracker(
                country_iso_code=self.country_iso,
                save_to_file=False,
                log_level="error",
                measure_power_secs=1,
            )
            self._tracker.start()
            self._tracker_active = True
            logger.info("CodeCarbon OfflineEmissionsTracker started successfully.")
        except Exception as e:
            logger.warning("Could not start CodeCarbon tracker: %s. Using fallback modeling.", e)
            self._tracker = None
            self._tracker_active = False

    def start_measurement(self, task_name: Optional[str] = None) -> str:
        """Begins tracking a workload task."""
        t_id = task_name or f"rag_task_{uuid.uuid4().hex[:8]}"
        if self._tracker and self._tracker_active:
            try:
                self._tracker.start_task(t_id)
            except Exception as e:
                logger.debug("CodeCarbon start_task notice: %s", e)
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
            E = Energy in kWh (directly measured via CodeCarbon when available,
                or explicitly labeled modeled estimate for sub-millisecond cache hits)
            I = Grid carbon intensity (gCO2eq/kWh)
            M = Embodied carbon in gCO2eq (amortized hardware baseline model)
            R = Functional unit (1 query)
        """
        self.total_queries += 1

        energy_kwh = 0.0
        raw_emissions_kg = 0.0
        duration_sec = max(fallback_duration_sec, 0.0001)
        cpu_power_w = 0.0
        ram_power_w = 0.0
        is_directly_measured = False
        measurement_type = "unavailable"
        measurement_note = ""

        # Step 1: Query CodeCarbon if active
        if self._tracker and self._tracker_active:
            try:
                emissions_data = self._tracker.stop_task(task_name)
                if emissions_data:
                    raw_energy = float(emissions_data.energy_consumed or 0.0)
                    raw_emissions_kg = float(emissions_data.emissions or 0.0)
                    duration_sec = max(float(emissions_data.duration or duration_sec), 0.0001)
                    cpu_power_w = float(emissions_data.cpu_power or 0.0)
                    ram_power_w = float(emissions_data.ram_power or 0.0)

                    if raw_energy > 0.0:
                        is_directly_measured = True
                        measurement_type = "codecarbon_tracked"
                        measurement_note = "Directly tracked via CodeCarbon hardware power/load monitoring."
            except Exception as e:
                logger.warning("Error reading CodeCarbon task '%s': %s", task_name, e)

        # Step 2: Handle sub-millisecond cache hits or sensor zero-readings honestly
        directly_measured_energy_kwh: Optional[float] = None
        estimated_energy_kwh: Optional[float] = None

        if is_directly_measured:
            directly_measured_energy_kwh = raw_energy
            energy_kwh = raw_energy
        else:
            # Model energy based on baseline idle system power
            modeled_power_w = max(cpu_power_w + ram_power_w, IDLE_SYSTEM_POWER_WATTS)
            energy_kwh = (modeled_power_w * duration_sec) / 3600000.0
            estimated_energy_kwh = energy_kwh
            if is_cache_hit:
                measurement_type = "modeled_estimate"
                measurement_note = (
                    "Cache hit duration fell below hardware sensor resolution threshold; "
                    "energy is modeled using measured idle power baseline."
                )
            else:
                measurement_type = "modeled_fallback"
                measurement_note = "Sensor returned zero delta; energy estimated using processor load model."

        # Step 3: Compute Operational Emissions (O = E * I)
        if is_directly_measured and raw_emissions_kg > 0.0:
            operational_co2_g = raw_emissions_kg * 1000.0
        else:
            operational_co2_g = energy_kwh * DEFAULT_GRID_INTENSITY_G_PER_KWH

        # Step 4: Compute Embodied Carbon (M) per GSF guidelines
        embodied_co2_g = EMBODIED_RATE_G_PER_SEC * duration_sec

        # Step 5: Compute Total SCI Score (R = 1 query)
        sci_score = operational_co2_g + embodied_co2_g

        # Step 6: Accumulate session counters
        if is_cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self._last_uncached_energy_kwh = energy_kwh
            self._last_uncached_sci_g = sci_score

        self.cumulative_energy_kwh += energy_kwh
        if is_directly_measured:
            self.cumulative_directly_measured_kwh += energy_kwh
        else:
            self.cumulative_modeled_energy_kwh += energy_kwh

        self.cumulative_operational_co2_g += operational_co2_g
        self.cumulative_embodied_co2_g += embodied_co2_g
        self.cumulative_sci_g_co2 += sci_score

        # Step 7: Calculate savings compared to the last uncached query
        energy_saved_kwh = 0.0
        emissions_saved_g = 0.0
        if is_cache_hit and self._last_uncached_energy_kwh > 0.0:
            energy_saved_kwh = max(0.0, self._last_uncached_energy_kwh - energy_kwh)
            emissions_saved_g = max(0.0, self._last_uncached_sci_g - sci_score)
            self.cumulative_energy_saved_kwh += energy_saved_kwh
            self.cumulative_emissions_avoided_g_co2 += emissions_saved_g

        status_desc = (
            "Directly measured via CodeCarbon"
            if is_directly_measured
            else ("Modeled estimate (sub-millisecond cache hit)" if is_cache_hit else "Modeled estimate (sensor fallback)")
        )

        return {
            "is_cache_hit": is_cache_hit,
            "duration_ms": round(duration_sec * 1000.0, 2),
            "energy_kwh": float(f"{energy_kwh:.10f}"),
            "directly_measured_energy_kwh": float(f"{directly_measured_energy_kwh:.10f}") if directly_measured_energy_kwh is not None else None,
            "estimated_energy_kwh": float(f"{estimated_energy_kwh:.10f}") if estimated_energy_kwh is not None else None,
            # measured_energy_kwh is strictly populated ONLY when directly measured; otherwise None.
            "measured_energy_kwh": float(f"{directly_measured_energy_kwh:.10f}") if directly_measured_energy_kwh is not None else None,
            "energy_is_directly_measured": is_directly_measured,
            "energy_measurement_type": measurement_type,
            "energy_measurement_status": status_desc,
            "measurement_notes": measurement_note,
            "estimated_operational_co2_g": float(f"{operational_co2_g:.8f}"),
            "operational_co2_g": float(f"{operational_co2_g:.8f}"),
            "assumed_embodied_co2_g": float(f"{embodied_co2_g:.8f}"),
            "embodied_co2_g": float(f"{embodied_co2_g:.8f}"),
            "sci_score_g_co2_per_query": float(f"{sci_score:.8f}"),
            "power_telemetry": {
                "cpu_power_watts": round(cpu_power_w, 2),
                "ram_power_watts": round(ram_power_w, 2),
            },
            "savings_vs_last_uncached": {
                "energy_saved_kwh": float(f"{energy_saved_kwh:.10f}"),
                "emissions_avoided_g": float(f"{emissions_saved_g:.8f}"),
            },
            "energy_saved_vs_baseline_kwh": float(f"{energy_saved_kwh:.10f}"),
            "emissions_saved_g": float(f"{emissions_saved_g:.8f}"),
            "methodology": {
                "energy_source": (
                    "Direct CodeCarbon workload task tracking"
                    if is_directly_measured
                    else "Explicit modeled estimate based on CPU idle/RAM power"
                ),
                "grid_intensity_source": f"CodeCarbon regional factor for {self.country_iso} (~{DEFAULT_GRID_INTENSITY_G_PER_KWH} gCO2eq/kWh)",
                "embodied_carbon_basis": f"GSF amortized client device model ({EMBODIED_RATE_G_PER_SEC} gCO2eq/s based on 300kg CO2eq over 4-year lifespan)",
                "sci_standard": "GSF SCI = ((E * I) + M) / R (R = 1 query)",
                "measurement_boundary": "Local machine CPU and RAM execution only. Excludes network transmission and cloud datacenter PUE.",
            },
            "limitations": [
                "Windows CPU power on this architecture uses CodeCarbon's CPU TDP and load modeling (Intel RAPL registers are restricted without admin/bare-metal hypervisor).",
                "Sub-millisecond cache hits fall below physical sensor polling intervals and are explicitly modeled using idle baseline power.",
                "Embodied carbon (M) is an amortized model assumption per GSF specifications and cannot be metered by hardware sensors.",
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
            "cumulative_total_energy_kwh": float(f"{self.cumulative_energy_kwh:.10f}"),
            "cumulative_energy_kwh": float(f"{self.cumulative_energy_kwh:.10f}"),
            "cumulative_directly_measured_energy_kwh": float(f"{self.cumulative_directly_measured_kwh:.10f}"),
            "cumulative_directly_measured_kwh": float(f"{self.cumulative_directly_measured_kwh:.10f}"),
            "cumulative_modeled_energy_kwh": float(f"{self.cumulative_modeled_energy_kwh:.10f}"),
            "cumulative_operational_co2_g": float(f"{self.cumulative_operational_co2_g:.8f}"),
            "cumulative_embodied_co2_g": float(f"{self.cumulative_embodied_co2_g:.8f}"),
            "cumulative_sci_g_co2": float(f"{self.cumulative_sci_g_co2:.8f}"),
            "average_sci_g_co2_per_query": avg_sci,
            "cumulative_energy_saved_kwh": float(f"{self.cumulative_energy_saved_kwh:.10f}"),
            "cumulative_emissions_avoided_g_co2": float(f"{self.cumulative_emissions_avoided_g_co2:.8f}"),
            "energy_accounting_note": "Directly tracked energy is metered via CodeCarbon tasks; modeled energy accounts for sub-millisecond cache hits below physical sensor resolution.",
            "measurement_backend": "CodeCarbon OfflineEmissionsTracker" if self._tracker_active else "Hardware Model Fallback",
            "country_iso": self.country_iso,
        }

    def reset_stats(self):
        """Resets cumulative counters."""
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.cumulative_energy_kwh = 0.0
        self.cumulative_directly_measured_kwh = 0.0
        self.cumulative_modeled_energy_kwh = 0.0
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
                logger.debug("CodeCarbon shutdown notice: %s", e)
