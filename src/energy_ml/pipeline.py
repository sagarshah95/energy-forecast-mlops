"""Deterministic local ETL pipeline with atomic output replacement.

Week 3: Parquet + manifest. Week 15: this is the recovery unit — rerun the whole
job; there is no run_id in paths yet (Airflow writes the same data/ directory).
"""
import json
import logging
from pathlib import Path
from energy_ml.generate import generate_demand
from energy_ml.ingest import ingest_csv
from energy_ml.validation import validate_demand
from energy_ml.features import build_features

LOG = logging.getLogger(__name__)


def _write_parquet_atomic(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.parquet")
    df.to_parquet(tmp, index=False)
    # Atomic on the same filesystem only. Cross-device replace becomes copy+delete
    # and readers can see a partial file. Object storage needs a new key + pointer.
    tmp.replace(path)


def run_pipeline(days: int = 365, output_dir: str = "data", input_csv: str | None = None) -> dict:
    root = Path(output_dir)
    raw = ingest_csv(input_csv) if input_csv else generate_demand(days=days)
    validate_demand(raw)
    engineered = build_features(raw)
    # 168 lag hours + current row: need 169 raw hours before dropna leaves any rows.
    if engineered.empty:
        raise ValueError("Need at least 169 hourly observations per region")
    raw_path = root / "raw" / "demand.parquet"
    feature_path = root / "processed" / "features.parquet"
    _write_parquet_atomic(raw, raw_path)
    _write_parquet_atomic(engineered, feature_path)
    manifest = {"raw_rows": len(raw), "feature_rows": len(engineered),
                "source": str(input_csv) if input_csv else "synthetic:seed=42",
                "raw_path": str(raw_path), "features_path": str(feature_path),
                "forecast_horizon_hours": 1}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    LOG.info("Pipeline completed: %s", manifest)
    return manifest
