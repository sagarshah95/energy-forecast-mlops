"""Optional real CSV ingestion; caller must map fields to the documented contract.

Week 2/3: this adapter does not reshape EIA files. Map columns first, then call here.
"""
from pathlib import Path
import pandas as pd
from energy_ml.validation import validate_demand


def ingest_csv(path: str | Path) -> pd.DataFrame:
    # Required columns: timestamp, region_id, temperature_c, demand_mw.
    df = pd.read_csv(path)
    # Naive timestamps are labeled UTC. errors="raise" fails on unparseable values
    # instead of inserting NaT that would later trip the null check.
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    validate_demand(df)
    return df
