import os
import time
from typing import Any, Dict

from openai import OpenAI


BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


SYSTEM_PROMPT_RU = (
    "Ты аналитик. Отвечай кратко и по делу. Используй только факты из ввода. "
    "Если чего-то нет во входных данных — не выдумывай."
)

SYSTEM_PROMPT_EN = (
    "You are an analyst. Be brief and factual. Use only provided facts. "
    "Do not speculate beyond the input."
)


def _build_user_prompt(metrics: Dict[str, Any], forecast: Dict[str, Any]) -> str:
    return (
        f"Metrics: {metrics}. "
        f"Forecast: method={forecast.get('method')}, points={len(forecast.get('points', []))}."
    )


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


