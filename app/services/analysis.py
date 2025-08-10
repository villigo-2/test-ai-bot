from typing import Any, Dict

import pandas as pd
import numpy as np


def compute_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    series = df["value"].astype(float)

    mean_value = float(series.mean())
    median_value = float(series.median())
    std_value = float(series.std(ddof=0))
    min_value = int(series.min())
    max_value = int(series.max())

    num_points = len(series)
    segment_size = max(1, num_points // 5)
    start_mean = float(series.iloc[:segment_size].mean())
    end_mean = float(series.iloc[-segment_size:].mean())
    diff = end_mean - start_mean
    trend = "up" if diff > 5 else ("down" if diff < -5 else "flat")

    lag = 7
    try:
        inferred = pd.infer_freq(df.index)
        if inferred and inferred.startswith("W"):
            lag = 4
        elif inferred and inferred.startswith("D"):
            lag = 7
    except Exception:
        pass

    seasonality_hint = False
    if num_points > lag + 5:
        ac = series.autocorr(lag=lag)
        seasonality_hint = bool(ac is not None and ac > 0.3)

    peaks_count = int((series > (mean_value + std_value)).sum())

    return {
        "mean": mean_value,
        "median": median_value,
        "std": std_value,
        "min": min_value,
        "max": max_value,
        "trend": trend,
        "seasonality_hint": seasonality_hint,
        "peaks_count": peaks_count,
    }


def compute_simple_forecast(
    df: pd.DataFrame, horizon: int = 8, method: str = "linear"
) -> Dict[str, Any]:
    series = df["value"].astype(float).reset_index(drop=True)
    num_points = len(series)
    if num_points < 3 or horizon <= 0:
        return {"method": method, "horizon": horizon, "points": [], "note": "insufficient data"}

    if method == "naive":
        forecast_values = [float(series.iloc[-1])] * horizon
    else:
        x = np.arange(num_points, dtype=float)
        a, b = np.polyfit(x, series.values, deg=1)
        x_future = np.arange(num_points, num_points + horizon, dtype=float)
        forecast_values = list((a * x_future + b).clip(min=0, max=100))
        method = "linear"

    idx = pd.to_datetime(df.index)
    inferred = pd.infer_freq(idx) or "D"
    if inferred.startswith("W"):
        step = pd.Timedelta(days=7)
    elif inferred.startswith("M"):
        step = pd.DateOffset(months=1)
    else:
        step = pd.Timedelta(days=1)

    dates = []
    current = idx[-1]
    for _ in range(horizon):
        current = current + step
        dates.append(pd.Timestamp(current))

    return {
        "method": method,
        "horizon": horizon,
        "points": list(zip(dates, forecast_values)),
        "note": "simple forecast; low accuracy",
    }

