from typing import Any, Dict

import pandas as pd


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


