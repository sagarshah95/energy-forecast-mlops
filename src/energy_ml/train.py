"""Chronological model training and seasonal-naive benchmark.

Week 8–9: single 80/20 holdout, not walk-forward. If model MAE > baseline MAE,
record it — do not claim improvement. joblib/pickle: load only trusted files.
"""
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from energy_ml.features import FEATURES


def train_model(data_dir: str = "data", artifact_dir: str = "artifacts",
                track_mlflow: bool = False) -> dict:
    df = pd.read_parquet(Path(data_dir) / "processed" / "features.parquet")
    df = df.sort_values("timestamp").reset_index(drop=True)
    if len(df) < 100:
        raise ValueError("Not enough feature rows to evaluate")
    split = int(len(df) * 0.8)
    train, test = df.iloc[:split], df.iloc[split:]
    # Row fraction is chronological for ONE region. Multi-region interleaving can
    # put later timestamps in train and earlier ones in test — fail instead.
    if train["timestamp"].max() >= test["timestamp"].min():
        raise ValueError("Train/test overlap: use a date-based split for multi-region data")
    model = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.07,
                                           random_state=42)
    model.fit(train[FEATURES], train["target_demand_mw"])
    predicted = model.predict(test[FEATURES])
    actual = test["target_demand_mw"]
    # Seasonal naive: same hour yesterday. Strong baseline on diurnal synthetic data.
    baseline = test["demand_lag_24h"]
    metrics = {"model_mae": float(mean_absolute_error(actual, predicted)),
               "model_rmse": float(root_mean_squared_error(actual, predicted)),
               "baseline_mae": float(mean_absolute_error(actual, baseline)),
               "baseline_rmse": float(root_mean_squared_error(actual, baseline)),
               "train_rows": len(train), "test_rows": len(test)}
    out = Path(artifact_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Bundle features with the model so /predict can reindex columns in train order.
    joblib.dump({"model": model, "features": FEATURES, "metrics": metrics}, out / "model.joblib")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    if track_mlflow:
        import mlflow
        import mlflow.sklearn
        mlflow.set_experiment("energy-demand-forecasting")
        with mlflow.start_run():
            mlflow.log_params({"max_iter": 150, "learning_rate": 0.07})
            mlflow.log_metrics({k: v for k, v in metrics.items() if "rows" not in k})
            # Registry aliases / champion promotion are Week 13 work; this only logs a run.
            mlflow.sklearn.log_model(model, name="energy-model")
    return metrics
