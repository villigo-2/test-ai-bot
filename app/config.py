import os
from dataclasses import dataclass
from typing import Final

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # dotenv опционален в dev; игнорируем, если недоступен
    pass


@dataclass(frozen=True)
class Settings:
    bot_token: str


_REQUIRED_ENV: Final[list[str]] = ["BOT_TOKEN"]


def get_settings() -> Settings:
    for var in _REQUIRED_ENV:
        if not os.getenv(var):
            raise RuntimeError(f"Missing required env var: {var}")
    return Settings(bot_token=os.environ["BOT_TOKEN"])


