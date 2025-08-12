from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "Привет! Я бот-аналитик Google Trends.\n"
        "Формат запроса: запрос; период; страна\n"
        "Пример: iphone; 12m; Азербайджан\n\n"
        "Справка: /help"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    await message.answer(
        "Формат: <запрос>; <период>; <страна>\n"
        "Периоды: 7d, 30d, 12m, 5y, all\n"
        "Пример: iphone; 12m; Азербайджан\n\n"
    )


from app.bot.parser import parse_user_input, try_parse_timeframe
from app.services.trends_client import fetch_interest_over_time
from app.services.analysis import compute_metrics, compute_simple_forecast
from app.services.plot import render_trend_plot
from app.services.llm_client import summarize
from app.bot.state import add_message, get_recent, set_last_context, get_last_context


@router.message()
async def handle_query(message: types.Message) -> None:
    try:
        # Поддержка смены периода одним сообщением: "7d"/"30d"/"12m"/"5y"/"all"
        only_tf = try_parse_timeframe(message.text or "")
        if only_tf:
            last = get_last_context(message.chat.id)
            if not last:
                raise ValueError("Сначала пришлите полный запрос: <запрос>; <период>; <страна>")
            query, geo_iso = last
            parsed_query = type("PQ", (), {"query": query, "geo_iso": geo_iso, "timeframe": only_tf, "country": ""})
        else:
            parsed_query = parse_user_input(message.text or "")
            set_last_context(message.chat.id, parsed_query.query, parsed_query.geo_iso)
        add_message(message.chat.id, "user", message.text or "")
        parsed = parsed_query
        df = fetch_interest_over_time(parsed.query, parsed.geo_iso, parsed.timeframe)
        points = len(df)
        date_min = df.index.min().date()
        date_max = df.index.max().date()
        country_mark = parsed.geo_iso or "world"
        metrics = compute_metrics(df)
        forecast = compute_simple_forecast(df, horizon=8, method="linear")
        await message.answer(
            f"Запрос: {parsed.query}\n"
            f"Период: {parsed.timeframe}\n"
            f"Страна: {parsed.country} → {country_mark}\n"
            f"Точек: {points}\n"
            f"Диапазон: {date_min} — {date_max}\n"
            f"Метрики: mean={metrics['mean']:.1f}, median={metrics['median']:.1f}, std={metrics['std']:.1f}, "
            f"min={metrics['min']}, max={metrics['max']}, trend={metrics['trend']}, "
            f"seasonality_hint={metrics['seasonality_hint']}, peaks={metrics['peaks_count']}\n"
            f"Прогноз: метод={forecast['method']}, точек={len(forecast['points'])}"
        )

        # Отправка графика как фото
        try:
            png_bytes = render_trend_plot(df, forecast)
            caption = (
                f"{parsed.query} | {parsed.timeframe} | {country_mark}\n"
                f"Период: {date_min} — {date_max}"
            )
            await message.answer_photo(types.BufferedInputFile(png_bytes, filename="trend.png"), caption=caption)
        except Exception:
            # График опционален: не падаем, если не удалось сгенерировать
            pass

        # Краткое резюме через LLM
        try:
            history = get_recent(message.chat.id, limit=3)
            summary = summarize(metrics, forecast, locale="ru", history=history)
            if summary:
                await message.answer(f"<b>Резюме:</b>\n{summary}", parse_mode=ParseMode.HTML)
                add_message(message.chat.id, "assistant", summary)
        except Exception:
            # На MVP при сбое LLM просто пропускаем резюме
            pass
    except Exception as e:
        await message.answer(
            "Ожидаю формат: <запрос>; <период>; <страна>\n"
            "Периоды: 7d, 30d, 12m, 5y, all\n"
            "Пример: iphone; 12m; Азербайджан\n\n"
            f"Ошибка: {e}"
        )

