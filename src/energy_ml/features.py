"""One-hour-ahead supervised features; only prior demand observations are used.

Target timestamp t is the hour being predicted. Forecast origin is t-1:
lags and the rolling mean must not include demand at t (or later).
SQL twin: sql/features.sql. Leakage test: tests/test_core.py::test_no_future_leakage.
Keep FEATURES in sync with api.ForecastInput.
"""
import numpy as np
import pandas as pd

# Serving, training, and the smoke test all import this list. Do not add
# temperature_c: it is observed at t, not an as-of weather forecast.
FEATURES = ["demand_lag_1h", "demand_lag_24h", "demand_lag_168h",
            "rolling_mean_24h", "hour_sin", "hour_cos", "day_of_week"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    # Partition by region so lag(1) never crosses a region boundary (same as SQL WINDOW).
    for _, g in df.groupby("region_id", sort=True):
        g = g.sort_values("timestamp").copy()
        for lag in (1, 24, 168):
            g[f"demand_lag_{lag}h"] = g["demand_mw"].shift(lag)
        # shift(1) BEFORE rolling: window is t-24..t-1, not t-23..t.
        # Dropping shift(1) would fail test_no_future_leakage.
        g["rolling_mean_24h"] = g["demand_mw"].shift(1).rolling(24).mean()
        hour = g["timestamp"].dt.hour
        # Cyclical encoding so hour 23 is close to hour 0 (unlike a raw integer).
        g["hour_sin"] = np.sin(2 * np.pi * hour / 24)
        g["hour_cos"] = np.cos(2 * np.pi * hour / 24)
        g["day_of_week"] = g["timestamp"].dt.dayofweek
        # Horizon = 1h: label is demand at t. Multi-horizon would use shift(-h) and
        # still compute features at the origin only.
        g["target_demand_mw"] = g["demand_mw"]
        parts.append(g)
    # Longest lag is 168h, so the first week per region is dropped.
    # 365 days -> 8760 raw, 8592 feature rows (see README / test_end_to_end).
    return pd.concat(parts, ignore_index=True).dropna(subset=FEATURES).reset_index(drop=True)
