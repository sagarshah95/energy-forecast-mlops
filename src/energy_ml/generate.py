"""Deterministic synthetic hourly energy data; NOT a real utility dataset.

Week 1: seed + UTC timestamps so tests can assert frame equality.
Week 7: temperature_c is generated with demand but must NOT be used as a
model feature — it is observed weather at time t, not a forecast vintage.
"""
import numpy as np
import pandas as pd


def generate_demand(days: int = 365, seed: int = 42, region: str = "TX_NORTH") -> pd.DataFrame:
    if days <= 0:
        raise ValueError("days must be positive")
    # Generator API (not np.random.seed) keeps this function isolated from global RNG state.
    rng = np.random.default_rng(seed)
    n = days * 24
    # tz="UTC" is required: validate_demand rejects naive timestamps (DST would also
    # break the exact 1-hour continuity check).
    timestamps = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    hour = timestamps.hour.to_numpy()
    weekday = timestamps.dayofweek.to_numpy()
    t = np.arange(n)
    # Seasonal + diurnal temperature plus noise. Coupled into demand below.
    temperature = (22 + 7 * np.sin(2 * np.pi * t / (365 * 24))
                   + 4 * np.sin(2 * np.pi * (hour - 8) / 24)
                   + rng.normal(0, 1.5, n))
    # Diurnal sine, weekend drop, heating/cooling vs 21 C, Gaussian noise ~30 MW.
    demand = (1300 + 160 * np.sin(2 * np.pi * (hour - 9) / 24)
              + np.where(weekday >= 5, -90, 0)
              + 14 * np.abs(temperature - 21) + rng.normal(0, 30, n))
    # Column names are the ingest contract (see validation.REQUIRED).
    return pd.DataFrame({"timestamp": timestamps, "region_id": region,
                         "temperature_c": temperature, "demand_mw": demand})
