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
        # Public URL for the webhook.
        # Format: https://<service-name>-<project-hash>-<region>.a.run.app
        project_id = os.environ.get("GCP_PROJECT_ID")
        region = os.environ.get("GCP_REGION")
        service_name = os.environ.get("GCP_SERVICE_NAME", "telegram-bot")

        if project_id and region:
             webhook_url = f"https://{service_name}-{project_id}-{region}.a.run.app{webhook_path}"
        else:
            # Fallback for other hosting or manual URL
            webhook_url = os.environ.get("WEBHOOK_URL", "")
    else:
        # For local development, we use polling, so webhook settings are not critical.
        port = int(os.environ.get("PORT", 8080))
        host = os.environ.get("WEB_SERVER_HOST", "127.0.0.1")
        webhook_path = os.environ.get("WEBHOOK_PATH", "/webhook")
        webhook_url = os.environ.get("WEBHOOK_URL", "") # Only if you use ngrok locally

    return Settings(
        bot_token=os.environ["BOT_TOKEN"],
        web_server_host=host,
        web_server_port=port,
        webhook_path=webhook_path,
        webhook_url=webhook_url,
    )


