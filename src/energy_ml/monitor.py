"""Offline prediction monitoring once actual demand labels become available.

Week 21: compare recent MAE to the holdout reference (metrics.json model_mae),
not to zero. Labels for hour t arrive after publication delay — do not score
at forecast origin. This is not feature-drift detection.
"""
import numpy as np
from sklearn.metrics import mean_absolute_error


def evaluate_recent(actual, predicted, reference_mae: float, tolerance: float = 1.25) -> dict:
    if len(actual) == 0 or len(actual) != len(predicted):
        raise ValueError("Need equally sized nonempty arrays")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Non-finite monitoring input")
    mae = float(mean_absolute_error(actual, predicted))
    # 1.25x holdout MAE: flag regression, not every noisy hour (alert fatigue).
    return {"mae": mae, "reference_mae": reference_mae,
            "performance_alert": bool(mae > reference_mae * tolerance)}
