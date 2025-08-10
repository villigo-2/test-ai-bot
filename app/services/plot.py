from io import BytesIO
from typing import Any, Dict, Optional

import matplotlib


# Без дисплея (для серверов/контейнеров)
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def render_trend_plot(df: pd.DataFrame, forecast: Optional[Dict[str, Any]] = None) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(df.index, df["value"], label="interest", color="#1f77b4")

    if forecast and forecast.get("points"):
        dates, vals = zip(*forecast["points"])  # type: ignore
        ax.plot(dates, vals, label="forecast", color="#ff7f0e", linestyle="--")

    ax.set_xlabel("Date")
    ax.set_ylabel("Interest (0-100)")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


