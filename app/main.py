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


async def main() -> None:
    settings = get_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    if settings.is_production:
        logging.info("Starting webhook server")
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=settings.webhook_path)

        # Health check endpoint
        app.router.add_get("/healthz", lambda request: web.Response(text="OK"))

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=settings.web_server_host, port=settings.web_server_port)
        await site.start()

        logging.info(f"Web server is listening on {settings.web_server_host}:{settings.web_server_port}")
        await asyncio.Event().wait()  # Keep the server running
    else:
        logging.info("Starting polling")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


