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

### Google Cloud Run Deployment
1. **Prerequisites**:
   - Google Cloud SDK (`gcloud`) installed and configured.
   - A Google Cloud project with billing enabled.
   - Artifact Registry API and Cloud Build API enabled.
   - Run `gcloud auth login` and `gcloud config set project YOUR_PROJECT_ID`.
   - Create an Artifact Registry repository (run this command once):
     ```bash
     gcloud artifacts repositories create telegram-bot \
         --repository-format=docker \
         --location=europe-west1 \
         --description="Docker repository for Telegram bot"
     ```

2. **Setup Secrets (First Time Only)**:
   - Enable the Secret Manager API.
   - Create secrets for your bot token and API keys. This is the secure way to handle credentials.
     ```bash
     # Create bot token secret
     echo -n "YOUR_TELEGRAM_BOT_TOKEN" | \
       gcloud secrets create telegram-bot-token --data-file=- --project=umico-client

     # Create OpenRouter API key secret (optional)
     echo -n "YOUR_OPENROUTER_API_KEY" | \
       gcloud secrets create openrouter-api-key --data-file=- --project=umico-client
     ```
   - Grant the Cloud Run service account access to these secrets. Find your service account email (it looks like `service-<project-number>@gcp-sa-run.iam.gserviceaccount.com`) in the IAM section of the Google Cloud Console.
     ```bash
     gcloud secrets add-iam-policy-binding telegram-bot-token \
       --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
       --role="roles/secretmanager.secretAccessor" \
       --project=umico-client

     gcloud secrets add-iam-policy-binding openrouter-api-key \
       --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
       --role="roles/secretmanager.secretAccessor" \
       --project=umico-client
     ```

3. **Configuration**:
   - Create a `.env` file from `env.example` and fill in your `BOT_TOKEN` for local development.
   - In `env.example`, ensure your `GCP_PROJECT_ID` and `GCP_REGION` are set correctly.

4. **Build and Deploy**:
   - Run the Cloud Build pipeline:
     ```bash
     make cloud-build
     ```
   - This will build the Docker image, push it to Artifact Registry, and deploy it to Cloud Run.

5. **Set the Webhook**:
   - After deployment, Cloud Run will provide a service URL. It should look like: `https://telegram-bot-app-<project-hash>-<region>.a.run.app`.
   - Set the Telegram webhook to this URL:
     ```bash
     make set-telegram-webhook
     ```
   - You will be prompted to enter your bot token and the webhook URL. The webhook path is `/webhook` by default. Your full webhook URL will be `https://<service-url>/webhook`.

6. **Environment Variables**:
   - The deployment process automatically maps the secrets (`BOT_TOKEN`, `OPENROUTER_API_KEY`) to environment variables in Cloud Run.
   - You can add or modify other non-sensitive variables (like `OPENROUTER_MODEL`) directly in the Cloud Run service settings.

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


