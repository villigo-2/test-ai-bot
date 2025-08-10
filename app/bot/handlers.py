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
from app.services.trends_client import fetch_interest_over_time
from app.services.analysis import compute_metrics


@router.message()
async def handle_query(message: types.Message) -> None:
    try:
        parsed = parse_user_input(message.text or "")
        df = fetch_interest_over_time(parsed.query, parsed.geo_iso, parsed.timeframe)
        points = len(df)
        date_min = df.index.min().date()
        date_max = df.index.max().date()
        country_mark = parsed.geo_iso or "world"
        metrics = compute_metrics(df)
        await message.answer(
            f"Запрос: {parsed.query}\n"
            f"Период: {parsed.timeframe}\n"
            f"Страна: {parsed.country} → {country_mark}\n"
            f"Точек: {points}\n"
            f"Диапазон: {date_min} — {date_max}\n"
            f"Метрики: mean={metrics['mean']:.1f}, median={metrics['median']:.1f}, std={metrics['std']:.1f}, "
            f"min={metrics['min']}, max={metrics['max']}, trend={metrics['trend']}, "
            f"seasonality_hint={metrics['seasonality_hint']}, peaks={metrics['peaks_count']}"
        )
    except Exception as e:
        await message.answer(
            "Ожидаю формат: <запрос>; <период>; <страна>\n"
            "Периоды: 7d, 30d, 12m, 5y, all\n"
            "Пример: chatgpt; 12m; Казахстан\n\n"
            f"Ошибка: {e}"
        )

