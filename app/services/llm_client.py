import os
import time
import logging
import random
import pathlib
from typing import Any, Dict, List, Optional

from openai import OpenAI
from app.config import get_settings


def _get_client():
    """Get OpenAI client with current settings"""
    settings = get_settings()
    base_url = settings.openrouter_base_url or "https://openrouter.ai/api/v1"
    api_key = settings.openrouter_api_key or ""
    return OpenAI(
        base_url=base_url, 
        api_key=api_key,
        timeout=4.0  # Строгий таймаут для быстрого отклика
    )


def _get_model():
    """Get current model from settings"""
    settings = get_settings()
    return settings.openrouter_model or "gpt-4o-mini"


SYSTEM_PROMPT_RU = (
    "Ты аналитик. Дай краткий, фактический и структурированный ответ. "
    "Используй только переданные метрики и прогноз, не добавляй внешние данные и домыслы. Формат:\n"
    "1) 1–2 предложения о направлении тренда.\n"
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


def summarize(
    metrics: Dict[str, Any],
    forecast: Dict[str, Any],
    locale: str = "ru",
    history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    system_prompt = SYSTEM_PROMPT_RU if locale.lower().startswith("ru") else SYSTEM_PROMPT_EN
    user_prompt = _build_user_prompt(metrics, forecast)

    # Один ретрай с небольшим бэкофом
    for attempt in range(2):
        try:
            history_msgs: List[Dict[str, str]] = []
            for m in (history or []):
                role = "user" if (m.get("role") == "user") else "assistant"
                content = str(m.get("content") or "")[:500]
                if content:
                    history_msgs.append({"role": role, "content": content})
            t0 = time.perf_counter()
            client = _get_client()
            model = _get_model()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *history_msgs,
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                timeout=4,  # Быстрый отклик - 4 секунды максимум
            )
            text = (resp.choices[0].message.content or "").strip()
            latency_ms = int((time.perf_counter() - t0) * 1000)
            logging.info("llm.request done model=%s latency_ms=%d", model, latency_ms)

            # sampling
            sample_rate = float(os.getenv("LLM_SAMPLE_RATE", "0.1"))
            if random.random() < sample_rate:
                pathlib.Path("logs").mkdir(parents=True, exist_ok=True)
                with open("logs/llm_samples.log", "a", encoding="utf-8") as f:
                    f.write(f"PROMPT:\n{user_prompt}\n---\nANSWER:\n{text}\n===\n")
            return text or ""
        except Exception:
            if attempt == 0:
                time.sleep(0.2)  # Уменьшаем с 0.6 до 0.2 сек
            else:
                model = _get_model()
                logging.error("llm.request error model=%s attempt=%d", model, attempt + 1)
                return "Краткое резюме временно недоступно. Попробуйте ещё раз позже."

    return "Краткое резюме временно недоступно."


