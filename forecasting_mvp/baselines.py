"""Deterministic Phase 3 statistical baselines on an admitted past-only request."""
import math

from .prediction_input import PredictionInput

MODELS = ("persistence", "rolling_mean", "linear_trend")
CANDIDATES = (("persistence", 0), ("rolling_mean", 7), ("rolling_mean", 30),
              ("rolling_mean", 90), ("linear_trend", 30), ("linear_trend", 90))


def baseline_predict(request, model, window_days=0):
    """No dataset, measurement store or labels enter this function.

    Trend estimates OLS daily slope within the past window and anchors the
    extrapolation at the observed current stock. Raw predictions are retained;
    all scored stocks use the preregistered nonnegative clipping policy.
    """
    if not isinstance(request, PredictionInput):
        raise ValueError("An admitted PredictionInput is required")
    if (model, window_days) not in CANDIDATES:
        raise ValueError("Unregistered baseline candidate")
    payload = request.model_payload()
    values, horizon = payload["past_values"], payload["horizon_days"]
    current = values[-1]
    if current is None:
        raise ValueError("Known current stock required")
    if model == "persistence":
        raw = current
    else:
        points = [(i, v) for i, v in enumerate(values[-window_days:]) if v is not None]
        if len(values) < window_days or len(points) < math.ceil(.8 * window_days):
            raise ValueError("Insufficient registered historical window")
        mean = sum(v for _, v in points) / len(points)
        if model == "rolling_mean":
            raw = mean
        else:
            x_mean = sum(i for i, _ in points) / len(points)
            denom = sum((i - x_mean)**2 for i, _ in points)
            if not denom:
                raise ValueError("Trend needs distinct past timestamps")
            slope = sum((i - x_mean) * (v - mean) for i, v in points) / denom
            raw = current + horizon * slope
    if not math.isfinite(raw):
        raise ValueError("Nonfinite baseline prediction")
    return float(raw), max(0.0, float(raw))
