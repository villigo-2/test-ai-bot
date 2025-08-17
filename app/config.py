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
    is_production: bool
    bot_token: str
    openrouter_api_key: str | None
    openrouter_model: str | None
    openrouter_base_url: str | None
    web_server_host: str
    web_server_port: int
    webhook_path: str
    webhook_url: str


_REQUIRED_ENV: Final[list[str]] = ["BOT_TOKEN"]


def get_settings() -> Settings:
    for var in _REQUIRED_ENV:
        if not os.getenv(var):
            raise RuntimeError(f"Missing required env var: {var}")
    # Webhook logic
    is_production = os.environ.get("ENV") == "production"
    webhook_url = ""

    if is_production:
        # Cloud Run/Heroku provide a PORT env var. Default to 8080.
        port = int(os.environ.get("PORT", 8080))
        host = os.environ.get("WEB_SERVER_HOST", "0.0.0.0")
        webhook_path = os.environ.get("WEBHOOK_PATH", "/webhook")
        # WEBHOOK_URL is not needed at startup in production anymore, it's set by the pipeline
        webhook_url = os.environ.get("WEBHOOK_URL", "")
    else:
        # For local development, we use polling, so webhook settings are not critical.
        port = int(os.environ.get("PORT", 8080))
        host = os.environ.get("WEB_SERVER_HOST", "127.0.0.1")
        webhook_path = os.environ.get("WEBHOOK_PATH", "/webhook")
        webhook_url = os.environ.get("WEBHOOK_URL", "")  # Only if you use ngrok locally

    return Settings(
        is_production=is_production,
        bot_token=os.environ["BOT_TOKEN"],
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openrouter_model=os.environ.get("OPENROUTER_MODEL"),
        openrouter_base_url=os.environ.get("OPENROUTER_BASE_URL"),
        web_server_host=host,
        web_server_port=port,
        webhook_path=webhook_path,
        webhook_url=webhook_url,
    )


