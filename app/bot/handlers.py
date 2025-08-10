from aiogram import Router, types
from aiogram.filters import Command


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "Привет! Я бот-аналитик Google Trends.\n"
        "Формат запроса: запрос; период; страна\n"
        "Пример: chatgpt; 12m; Казахстан\n\n"
        "Справка: /help"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    await message.answer(
        "Формат: <запрос>; <период>; <страна>\n"
        "Периоды: 7d, 30d, 12m, 5y, all\n"
        "Пример: chatgpt; 12m; Казахстан"
    )


from app.bot.parser import parse_user_input


@router.message()
async def handle_query(message: types.Message) -> None:
    try:
        parsed = parse_user_input(message.text or "")
        country_mark = parsed.geo_iso or "world"
        await message.answer(
            f"Запрос: {parsed.query}\nПериод: {parsed.timeframe}\nСтрана: {parsed.country} → {country_mark}"
        )
    except Exception:
        await message.answer(
            "Ожидаю формат: <запрос>; <период>; <страна>\n"
            "Периоды: 7d, 30d, 12m, 5y, all\n"
            "Пример: chatgpt; 12m; Казахстан"
        )

