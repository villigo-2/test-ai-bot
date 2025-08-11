import os
import time
from typing import Any, Dict

from openai import OpenAI


BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


SYSTEM_PROMPT_RU = (
    "Ты аналитик. Дай краткий, фактический и структурированный ответ. "
    "Используй только переданные метрики и прогноз, не добавляй внешние данные и домыслы. Формат:\n"
    "1) Резюме — 1–2 предложения о направлении тренда.\n"
    "2) Динамика — тренд (up/down/flat), стабильность/волатильность, пики, сезонность (если есть).\n"
    "3) Прогноз — ближайший горизонт: направление, ориентировочный диапазон значений и короткая интерпретация.\n"
    "4) Ограничения — источник (Google Trends, 0–100), простой метод прогноза, низкая точность.\n"
    "Пиши по‑русски, чётко и кратко, без категоричных формулировок и рекомендаций."
)

SYSTEM_PROMPT_EN = (
    "You are an analyst. Be brief and factual. Use only provided facts. "
    "Do not speculate beyond the input."
)


def _fmt_float(value: Any, digits: int = 1, default: str = "n/a") -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return default


def _fmt_int(value: Any, default: str = "n/a") -> str:
    try:
        return str(int(value))
    except Exception:
        return default


def _build_user_prompt(metrics: Dict[str, Any], forecast: Dict[str, Any]) -> str:
    mean_v = _fmt_float(metrics.get("mean"))
    med_v = _fmt_float(metrics.get("median"))
    std_v = _fmt_float(metrics.get("std"))
    min_v = _fmt_int(metrics.get("min"))
    max_v = _fmt_int(metrics.get("max"))
    trend = str(metrics.get("trend", "n/a"))
    seas = bool(metrics.get("seasonality_hint", False))
    peaks = _fmt_int(metrics.get("peaks_count"))

    points = forecast.get("points") or []
    method = str(forecast.get("method", "n/a"))
    horizon = _fmt_int(forecast.get("horizon"))

    if points:
        try:
            values = [float(v) for _, v in points]
        except Exception:
            values = []
    else:
        values = []

    first = _fmt_float(values[0]) if values else "n/a"
    last = _fmt_float(values[-1]) if values else "n/a"
    fmin = _fmt_float(min(values)) if values else "n/a"
    fmax = _fmt_float(max(values)) if values else "n/a"

    lines = [
        (
            "Данные: "
            f"mean={mean_v}, median={med_v}, std={std_v}, min={min_v}, max={max_v}, "
            f"trend={trend}, seasonality_hint={seas}, peaks_count={peaks}."
        ),
        (
            "Прогноз: "
            f"method={method}, horizon={horizon}, first≈{first}, last≈{last}, expected_range≈{fmin}–{fmax}."
        ),
    ]
    return "\n".join(lines)


def summarize(metrics: Dict[str, Any], forecast: Dict[str, Any], locale: str = "ru") -> str:
    system_prompt = SYSTEM_PROMPT_RU if locale.lower().startswith("ru") else SYSTEM_PROMPT_EN
    user_prompt = _build_user_prompt(metrics, forecast)

    # Один ретрай с небольшим бэкофом
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                timeout=15,
            )
            text = (resp.choices[0].message.content or "").strip()
            return text or ""
        except Exception:
            if attempt == 0:
                time.sleep(0.6)
            else:
                return "Краткое резюме временно недоступно. Попробуйте ещё раз позже."

    return "Краткое резюме временно недоступно."


