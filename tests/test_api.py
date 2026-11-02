"""API contract tests. Health does not require a trained model (lazy load)."""
from fastapi.testclient import TestClient
from energy_ml.api import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_input_validation():
    # Pydantic ge=0 on demand_lag_1h -> 422, not a 500 from the model.
    response = TestClient(app).post("/predict", json={"demand_lag_1h": -1})
    assert response.status_code == 422
