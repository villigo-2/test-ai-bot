from typing import Optional

import pandas as pd
from pytrends.request import TrendReq


_PYTRENDS_TIMEFRAME_MAP = {
    "7d": "now 7-d",
    "30d": "today 1-m",
    "12m": "today 12-m",
    "5y": "today 5-y",
    "all": "all",
}


def _normalize_timeframe(user_timeframe: str) -> str:
    tf = (user_timeframe or "").strip().lower()
    return _PYTRENDS_TIMEFRAME_MAP.get(tf, tf)


def fetch_interest_over_time(query: str, geo: str, timeframe: str, hl: str = "en-US") -> pd.DataFrame:
    """Получить временной ряд интереса 0–100 по запросу из Google Trends.

    Возвращает DataFrame с индексом datetime и одной колонкой 'value'.
    """
    pytrends = TrendReq(hl=hl, tz=0)
    tf_norm = _normalize_timeframe(timeframe)
    pytrends.build_payload([query], timeframe=tf_norm, geo=geo or "")
    df = pytrends.interest_over_time()
    if df is None or df.empty:
        raise ValueError("Данные не найдены для данного запроса/периода/региона")
    if query not in df.columns:
        raise ValueError("Неожиданный формат ответа Google Trends")
    series = df[query]
    out = pd.DataFrame({"value": series.astype(int)})
    out.index = pd.to_datetime(out.index)
    return out


