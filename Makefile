run:
	python -m app.main

docker-build:
	docker build -t test-ai-bot .

docker-run:
	docker run --rm --env-file .env test-ai-bot

# Google Cloud deployment
setup-secrets:
	@if [ ! -f .env ]; then echo "Error: .env file not found. Please create it from env.example"; exit 1; fi
	chmod +x setup-secrets.sh
	./setup-secrets.sh

cloud-build:
	@read -p "Enter GCP Project ID (e.g., my-gcp-project): " GCP_PROJECT_ID; \
	read -p "Enter GCP Region (e.g., europe-west1): " GCP_REGION; \
	read -p "Enter Service Name (e.g., telegram-bot-app): " SERVICE_NAME; \
	read -p "Enter Artifact Registry Repo Name (e.g., telegram-bot-app): " REPO_NAME; \
	gcloud builds submit --config cloudbuild.yaml \
		--substitutions=_SERVICE_NAME=$$SERVICE_NAME,_REGION=$$GCP_REGION,_REPO_NAME=$$REPO_NAME,SHORT_SHA=$$(git rev-parse --short HEAD) \
		--project=$$GCP_PROJECT_ID

# This command is no longer needed as the webhook and IAM permissions are set automatically in cloudbuild.yaml
set-telegram-webhook:
	@echo "Setting up Telegram webhook..."
	@read -p "Enter your bot token: " BOT_TOKEN; \
	read -p "Enter your webhook URL: " WEBHOOK_URL; \
	curl -F "url=$$WEBHOOK_URL" "https://api.telegram.org/bot$$BOT_TOKEN/setWebhook"
	