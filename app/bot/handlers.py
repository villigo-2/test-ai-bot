import logging
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
        "Периоды: 7d, 30d, 90d, 12m, 5y, all\n"
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
        user_text = message.text or ""
        chat_id = message.chat.id
        
        # Поддержка смены периода одним сообщением: "7d"/"30d"/"12m"/"5y"/"all"
        only_tf = try_parse_timeframe(user_text)
        if only_tf:
            last = get_last_context(chat_id)
            if not last:
                logging.warning("user.period_change_failed chat_id=%d text=%s reason=no_context", chat_id, user_text)
                raise ValueError("Сначала пришлите полный запрос: <запрос>; <период>; <страна>")
            query, geo_iso = last
            parsed_query = type("PQ", (), {"query": query, "geo_iso": geo_iso, "timeframe": only_tf, "country": ""})
            logging.info("user.period_change chat_id=%d query=%s timeframe=%s geo=%s", chat_id, query, only_tf, geo_iso)
        else:
            try:
                parsed_query = parse_user_input(user_text)
                set_last_context(chat_id, parsed_query.query, parsed_query.geo_iso)
                logging.info("user.query chat_id=%d query=%s timeframe=%s geo=%s country=%s", 
                           chat_id, parsed_query.query, parsed_query.timeframe, parsed_query.geo_iso, parsed_query.country)
            except Exception as parse_error:
                logging.error("user.parse_error chat_id=%d text=%s error=%s", chat_id, user_text, str(parse_error))
                raise
        
        add_message(chat_id, "user", user_text)
        parsed = parsed_query
        
        try:
            df = fetch_interest_over_time(parsed.query, parsed.geo_iso, parsed.timeframe)
            logging.info("trends.success chat_id=%d query=%s points=%d", chat_id, parsed.query, len(df))
        except Exception as trends_error:
            logging.error("trends.error chat_id=%d query=%s geo=%s timeframe=%s error=%s", 
                         chat_id, parsed.query, parsed.geo_iso, parsed.timeframe, str(trends_error))
            raise
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
        except Exception as llm_error:
            logging.warning("llm.summary_failed chat_id=%d error=%s", chat_id, str(llm_error))
            pass
    except Exception as e:
        logging.error("handler.error chat_id=%d text=%s error=%s", chat_id, user_text, str(e))
        await message.answer(
            "Ожидаю формат: <запрос>; <период>; <страна>\n"
            "Периоды: 7d, 30d, 12m, 5y, all\n"
            "Пример: chatgpt; 12m; Казахстан\n\n"
            f"Ошибка: {e}"
        )

