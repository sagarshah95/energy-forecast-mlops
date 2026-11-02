"""FastAPI inference service. Load ONLY trusted model artifacts.

Week 16: Pydantic contract, liveness vs readiness, 422 vs 503.
This endpoint expects precomputed FEATURES, not raw timestamps.
Do not expose publicly without auth, rate limits, and TLS (README).
"""
import os
from functools import lru_cache
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Energy Demand Forecast API", version="0.1.0")


class ForecastInput(BaseModel):
    # Field names and bounds must match energy_ml.features.FEATURES.
    demand_lag_1h: float = Field(ge=0)
    demand_lag_24h: float = Field(ge=0)
    demand_lag_168h: float = Field(ge=0)
    rolling_mean_24h: float = Field(ge=0)
    hour_sin: float = Field(ge=-1, le=1)
    hour_cos: float = Field(ge=-1, le=1)
    day_of_week: int = Field(ge=0, le=6)


@lru_cache(maxsize=1)
def get_bundle():
    # Lazy load so `from energy_ml.api import app` works in tests without a model.
    # Cache survives a file swap: restart workers or cache_clear() after deploy (Week 22).
    path = Path(os.getenv("ENERGY_MODEL_PATH", "artifacts/model.joblib"))
    if not path.exists():
        raise FileNotFoundError(f"Train model first; missing {path}")
    # pickle/joblib can execute code — only load artifacts from your train pipeline.
    return joblib.load(path)


@app.get("/health")
def health():
    """Liveness: process is up. Does not check the model file."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness: 503 if the model cannot be loaded (missing file, IO error)."""
    try:
        get_bundle()
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready"}


@app.post("/predict")
def predict(payload: ForecastInput):
    try:
        bundle = get_bundle()
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    record = payload.model_dump()
    # Reindex to the list stored with the model, not JSON key insertion order.
    X = pd.DataFrame([record], columns=bundle["features"])
    return {"predicted_demand_mw": float(bundle["model"].predict(X)[0]),
            "horizon_hours": 1}
