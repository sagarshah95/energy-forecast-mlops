"""Core contract, leakage, and pipeline tests (Weeks 1, 7, 8)."""
import pandas as pd
import pytest
from energy_ml.generate import generate_demand
from energy_ml.validation import DataValidationError, validate_demand
from energy_ml.features import build_features, FEATURES
from energy_ml.pipeline import run_pipeline
from energy_ml.train import train_model


def test_deterministic():
    """Same seed must reproduce the synthetic frame (portfolio evidence)."""
    pd.testing.assert_frame_equal(generate_demand(days=2), generate_demand(days=2))


def test_contract():
    df = generate_demand(days=2)
    validate_demand(df)
    df.loc[0, "demand_mw"] = -1
    with pytest.raises(DataValidationError, match="Negative"):
        validate_demand(df)


def test_missing_hour():
    df = generate_demand(days=2).drop(index=5)
    with pytest.raises(DataValidationError, match="irregular"):
        validate_demand(df)


def test_no_future_leakage():
    """Mutating demand after cutoff must not change features at t <= cutoff.

    Fails if rolling_mean_24h uses demand at t (missing shift(1) before rolling).
    """
    raw = generate_demand(days=12)
    original = build_features(raw)
    cutoff = raw["timestamp"].iloc[200]
    modified = raw.copy()
    modified.loc[modified["timestamp"] > cutoff, "demand_mw"] += 10000
    changed = build_features(modified)
    a = original.loc[original["timestamp"] <= cutoff, FEATURES].reset_index(drop=True)
    b = changed.loc[changed["timestamp"] <= cutoff, FEATURES].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_end_to_end(tmp_path):
    # 30 days * 24 hours = 720; drop 168-hour warmup -> 552 feature rows.
    manifest = run_pipeline(days=30, output_dir=str(tmp_path / "data"))
    assert manifest["feature_rows"] == 720 - 168
    metrics = train_model(str(tmp_path / "data"), str(tmp_path / "artifacts"))
    assert metrics["model_mae"] >= 0
    assert (tmp_path / "artifacts" / "model.joblib").exists()
