## Google Trends Analyst Bot (MVP)

Простой телеграм‑бот: получает запрос и период, забирает ряд из Google Trends, считает базовые метрики, строит краткий прогноз, присылает PNG‑график и лаконичное резюме через LLM (OpenRouter). KISS/MVP.

См. также: `@doc/vision.md`, `@doc/tasklist.md`.

### Требования
- Python 3.11
- Токен Telegram бота (`BOT_TOKEN`)
- Для LLM: ключ OpenRouter (`OPENROUTER_API_KEY`), модель (`OPENROUTER_MODEL`, напр. `gpt-4o-mini`)

### Быстрый старт (локально)
1) Конфиг
   - Скопируйте `env.example` → `.env` и заполните значения, либо экспортируйте переменные окружения:
     - `BOT_TOKEN`
     - `OPENROUTER_API_KEY` (опционально для LLM‑резюме)
     - `OPENROUTER_MODEL` (например, `gpt-4o-mini`)

2) Установка зависимостей
   - С `uv`:
     ```bash
     uv venv && source .venv/bin/activate
     uv pip install aiogram python-dotenv pytrends pandas numpy matplotlib openai
     ```
   - Или через `pip`:
     ```bash
     python3 -m venv .venv && source .venv/bin/activate
     pip install aiogram python-dotenv pytrends pandas numpy matplotlib openai
     ```

3) Запуск
   ```bash
   python -m app.main
   ```

### Использование в Telegram
- Команды: `/start`, `/help`
- Формат запроса: `запрос; период; страна`
  - Период: `7d`, `30d`, `12m`, `5y`, `all`
  - Пример: `chatgpt; 12m; Казахстан`
- Смена периода коротким сообщением: отправьте, например, `30d` — выполнится перерасчёт для последнего запроса

### Что присылает бот
- Краткая сводка: метрики (mean/median/std/min/max/trend/seasonality/peaks)
- Прогноз: метод (`linear`/`naive`), число точек, короткое резюме через LLM
- PNG‑график (ряд + при наличии прогноз)

### Переменные окружения
- `BOT_TOKEN` — токен Telegram бота (обязательно)
- `OPENROUTER_API_KEY` — ключ OpenRouter (для LLM‑резюме)
- `OPENROUTER_MODEL` — модель, напр. `gpt-4o-mini`
- `OPENROUTER_BASE_URL` — по умолчанию `https://openrouter.ai/api/v1`
- `LLM_SAMPLE_RATE` — доля сэмплируемых запросов для аудита (по умолчанию `0.1`)

### Логи и мониторинг LLM
- Логи в stdout/stderr (уровень по умолчанию `INFO`)
- Для LLM логируется `latency_ms`
- Сэмплирование 1 из N промптов в `logs/llm_samples.log` (без PII); настраивается `LLM_SAMPLE_RATE`

### Docker
```bash
make docker-build
BOT_TOKEN=xxx OPENROUTER_API_KEY=yyy OPENROUTER_MODEL=gpt-4o-mini make docker-run
```

### Структура
```
app/
  bot/
    handlers.py      # обработчики Telegram
    parser.py        # парсинг ввода и проверка периода
    state.py         # in-memory история
  services/
    trends_client.py # Google Trends (pytrends)
    analysis.py      # метрики и простой прогноз
    plot.py          # генерация PNG
    llm_client.py    # OpenRouter (OpenAI‑совместимый клиент)
  config.py          # чтение ENV
  main.py            # запуск бота (long polling)
```

### Известные ограничения (MVP)
- Google Trends — относительная шкала 0–100; нет официального API
- Прогноз простой (linear/naive), точность низкая
- История диалога — in‑memory (без БД)
- Нет сравнения терминов и расширенной аналитики

### Лицензирование/авторы
MVP для валидации идеи. См. `@doc/vision.md`.


