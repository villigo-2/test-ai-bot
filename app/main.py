import asyncio
import logging
import warnings
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from app.config import get_settings
from app.bot.handlers import router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

warnings.filterwarnings("ignore", category=FutureWarning, module="pytrends")


async def on_startup(bot: Bot, base_url: str, webhook_path: str):
    webhook_url = f"{base_url}{webhook_path}"
    await bot.set_webhook(webhook_url)


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


async def main() -> None:
    settings = get_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    if settings.webhook_url:
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=settings.webhook_path)
        setup_application(app, dp, bot=bot, base_url=settings.webhook_url, webhook_path=settings.webhook_path)

        # Health check endpoint
        app.router.add_get("/healthz", lambda request: web.Response(text="OK"))

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=settings.web_server_host, port=settings.web_server_port)
        await site.start()

        logging.info(f"Starting web server on {settings.web_server_host}:{settings.web_server_port}")
        await asyncio.Event().wait()  # Keep the server running
    else:
        logging.info("Starting polling")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


