from aiogram import Router, types
from aiogram.filters import Command


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "Привет! Я бот-аналитик Google Trends.\n"
        "Формат запроса: термин; период; страна\n"
        "Пример: chatgpt; 12m; Казахстан\n\n"
        "Справка: /help"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    await message.answer(
        "Формат: <термин>; <период>; <страна>\n"
        "Периоды: 7d, 30d, 12m, 5y, all\n"
        "Пример: chatgpt; 12m; Казахстан"
    )


