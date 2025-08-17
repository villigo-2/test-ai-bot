#!/bin/bash
set -e

PROJECT_ID="umico-client"
SERVICE_ACCOUNT="141614707906-compute@developer.gserviceaccount.com"

echo "Setting up secrets for Cloud Run deployment..."

# Function to parse .env values more robustly
parse_env_value() {
    local key="$1"
    local value=$(grep "^${key}=" .env | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
    echo "$value"
}

# Read .env file and create secrets
if [ -f ".env" ]; then
    echo "Reading .env file..."
    
    # Extract BOT_TOKEN
    BOT_TOKEN=$(parse_env_value "BOT_TOKEN")
    if [ ! -z "$BOT_TOKEN" ]; then
        echo "Creating telegram-bot-token secret..."
        echo -n "$BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=- --project=$PROJECT_ID 2>/dev/null || \
        echo -n "$BOT_TOKEN" | gcloud secrets versions add telegram-bot-token --data-file=- --project=$PROJECT_ID
        
        echo "Granting access to telegram-bot-token..."
        gcloud secrets add-iam-policy-binding telegram-bot-token \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor" \
            --project=$PROJECT_ID 2>/dev/null || true
    else
        echo "Warning: BOT_TOKEN not found or empty in .env file"
    fi
    
    # Extract OPENROUTER_API_KEY
    OPENROUTER_API_KEY=$(parse_env_value "OPENROUTER_API_KEY")
    if [ ! -z "$OPENROUTER_API_KEY" ]; then
        echo "Creating openrouter-api-key secret..."
        echo -n "$OPENROUTER_API_KEY" | gcloud secrets create openrouter-api-key --data-file=- --project=$PROJECT_ID 2>/dev/null || \
        echo -n "$OPENROUTER_API_KEY" | gcloud secrets versions add openrouter-api-key --data-file=- --project=$PROJECT_ID
        
        echo "Granting access to openrouter-api-key..."
        gcloud secrets add-iam-policy-binding openrouter-api-key \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor" \
            --project=$PROJECT_ID 2>/dev/null || true
    else
        echo "Warning: OPENROUTER_API_KEY not found or empty in .env file"
    fi
    
    echo "Secrets setup completed!"
else
    echo "No .env file found. Please create one with your secrets."
    exit 1
fi
