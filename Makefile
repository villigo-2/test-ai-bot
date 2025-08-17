run:
	python -m app.main

docker-build:
	docker build -t test-ai-bot .

docker-run:
	docker run --rm --env-file .env test-ai-bot

# Google Cloud deployment
cloud-build:
	gcloud builds submit --config cloudbuild.yaml .

set-telegram-webhook:
	@echo "Setting up Telegram webhook..."
	@read -p "Enter your bot token: " BOT_TOKEN; \
	read -p "Enter your webhook URL: " WEBHOOK_URL; \
	curl -F "url=$$WEBHOOK_URL" "https://api.telegram.org/bot$$BOT_TOKEN/setWebhook"


