import time
import random
import logging
from typing import Optional

import pandas as pd
from pytrends.request import TrendReq


_PYTRENDS_TIMEFRAME_MAP = {
    "7d": "now 7-d",
    "30d": "today 1-m",
    "90d": "today 3-m",
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
    max_retries = 3
    base_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            # Добавляем случайную задержку для избежания rate limiting
            if attempt > 0:
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0.5, 1.5)
                logging.info(f"trends.retry attempt={attempt + 1} delay={delay:.1f}s query={query}")
                time.sleep(delay)
            
            # Базовая задержка для уважения к rate limits даже при первом запросе
            if attempt == 0:
                time.sleep(random.uniform(0.5, 1.0))
            
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
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                if attempt < max_retries - 1:
                    logging.warning(f"trends.rate_limit attempt={attempt + 1} query={query} error={error_msg}")
                    continue
                else:
                    raise ValueError("Google Trends временно недоступен из-за ограничений запросов. Попробуйте через несколько минут.")
            else:
                # Для других ошибок не повторяем
                raise


