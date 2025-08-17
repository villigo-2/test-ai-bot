run:
	python -m app.main

docker-build:
	docker build -t test-ai-bot .

docker-run:
	docker run --rm --env-file .env test-ai-bot

# Google Cloud deployment
cloud-build:
	@if [ ! -f .env ]; then echo "Error: .env file not found. Please create it from env.example"; exit 1; fi
	chmod +x setup-secrets.sh
	gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(shell git rev-parse --short HEAD) .

set-telegram-webhook:
	@echo "Setting up Telegram webhook..."
	@read -p "Enter your bot token: " BOT_TOKEN; \
	read -p "Enter your webhook URL: " WEBHOOK_URL; \
	curl -F "url=$$WEBHOOK_URL" "https://api.telegram.org/bot$$BOT_TOKEN/setWebhook"


