"""Demonstrate delayed-label monitoring with simulated actual/predicted values.

reference_mae=20 is a demo threshold; production should use artifacts/metrics.json model_mae.
"""
import numpy as np
from energy_ml.monitor import evaluate_recent

rng = np.random.default_rng(42)
actual = np.array([1200., 1250., 1310., 1290.])
predicted = actual + rng.normal(0, 35, size=len(actual))
print(evaluate_recent(actual, predicted, reference_mae=20.0))
