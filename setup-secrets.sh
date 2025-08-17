#!/bin/bash
set -e

# Prompt for Project ID if not set
if [ -z "$GCP_PROJECT_ID" ]; then
    read -p "Enter your GCP Project ID: " GCP_PROJECT_ID
fi

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "Error: GCP Project ID is required."
    exit 1
fi

PROJECT_ID=$GCP_PROJECT_ID
echo "Using project ID: $PROJECT_ID"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
if [ -z "$PROJECT_NUMBER" ]; then
    echo "Error: Could not retrieve project number for project $PROJECT_ID."
    exit 1
fi

# Define service accounts
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
CLOUDRUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Setting up secrets for Cloud Run deployment..."
echo "Cloud Build Service Account: $CLOUDBUILD_SA"
echo "Cloud Run Service Account (default): $CLOUDRUN_SA"

# Function to parse .env values
parse_env_value() {
    local key="$1"
    grep "^${key}=" .env | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/^"\(.*\)"$/\1/;/^'"'"'\(.*\)'"'"'$/s//\1/'
}

# Function to create/update a secret and grant access
setup_secret() {
    local secret_name=$1
    local secret_value=$2

    if [ -z "$secret_value" ]; then
        echo "Warning: Value for $secret_name not found or empty in .env file"
        return
    fi

    echo "Creating/updating secret: $secret_name..."
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID
    else
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --replication-policy=automatic --project=$PROJECT_ID
    fi

    echo "Granting access to $secret_name for Cloud Build SA..."
    gcloud secrets add-iam-policy-binding $secret_name \
        --member="serviceAccount:$CLOUDBUILD_SA" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID --condition=None >/dev/null

    echo "Granting access to $secret_name for Cloud Run SA..."
    gcloud secrets add-iam-policy-binding $secret_name \
        --member="serviceAccount:$CLOUDRUN_SA" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID --condition=None >/dev/null
}

# Read .env file and process secrets
if [ -f ".env" ]; then
    BOT_TOKEN=$(parse_env_value "BOT_TOKEN")
    setup_secret "telegram-bot-token" "$BOT_TOKEN"

    OPENROUTER_API_KEY=$(parse_env_value "OPENROUTER_API_KEY")
    setup_secret "openrouter-api-key" "$OPENROUTER_API_KEY"

    echo "Secrets setup completed successfully!"
else
    echo "Error: .env file not found. Please create one from env.example."
    exit 1
fi
