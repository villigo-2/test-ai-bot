FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install uv and runtime deps (KISS)
RUN pip install --no-cache-dir uv
RUN uv pip install --no-cache-dir aiogram python-dotenv pytrends pandas numpy matplotlib openai

COPY app/ app/
COPY env.example ./

CMD ["python", "-m", "app.main"]


