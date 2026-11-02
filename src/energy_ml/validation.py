"""Fail-fast data contracts: timestamps, types, completeness, uniqueness.

Week 1–2: DataValidationError is an expected operational failure, not an assert
(asserts can be stripped with python -O). Tests: test_contract, test_missing_hour.
"""
import numpy as np
import pandas as pd


class DataValidationError(ValueError):
    """Raised when incoming data violates its schema or hourly continuity."""


REQUIRED = {"timestamp", "region_id", "temperature_c", "demand_mw"}


def validate_demand(df: pd.DataFrame) -> None:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise DataValidationError(f"Missing columns: {sorted(missing)}")
    if df.empty or df[list(REQUIRED)].isna().any().any():
        raise DataValidationError("Empty dataset or null required fields")
    # Timezone-aware dtype only. Naive datetime64[ns] is rejected even if values
    # look like UTC; generate.py sets tz="UTC" and ingest_csv uses utc=True.
    if not isinstance(df["timestamp"].dtype, pd.DatetimeTZDtype):
        raise DataValidationError("timestamp must be timezone-aware datetime")
    for column in ("demand_mw", "temperature_c"):
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise DataValidationError(f"{column} must be numeric")
        if not np.isfinite(df[column].to_numpy()).all():
            raise DataValidationError(f"{column} contains non-finite values")
    if (df["demand_mw"] < 0).any():
        raise DataValidationError("Negative demand")
    # Uniqueness is a contract, not only a warehouse unique index.
    if df.duplicated(["region_id", "timestamp"]).any():
        raise DataValidationError("Duplicate region-hour keys")
    # Per-region hourly continuity: a dropped hour fails (test_missing_hour).
    # DST gaps are why we require UTC rather than a local zone.
    for region, group in df.groupby("region_id"):
        times = group["timestamp"].sort_values()
        if not times.diff().dropna().eq(pd.Timedelta(hours=1)).all():
            raise DataValidationError(f"Missing or irregular hours: {region}")
