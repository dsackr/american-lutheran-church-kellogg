#!/usr/bin/env bash
# ==============================================================================
# Deploy American Lutheran Church Kellogg Website to Google Cloud Platform (GCP)
# ==============================================================================

set -e

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
REGION="us-west1"
SERVICE_NAME="alc-kellogg"

echo "=========================================================="
echo " American Lutheran Church Kellogg — GCP Deployment Script"
echo "=========================================================="
echo "Active GCP Account: $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
echo "Current GCP Project: ${PROJECT_ID:-[Not set]}"
echo ""

echo "Choose your GCP Serverless deployment method:"
echo " 1) Google Cloud Run (Serverless Container - Fast, auto-scaled, zero idle cost)"
echo " 2) Firebase Hosting (Google CDN Edge - Free tier, automatic SSL & custom domain redirects)"
echo " 3) Google Cloud Storage Bucket (Direct Static Site)"
echo ""
read -p "Select option [1-3] (Default: 1): " DEPLOY_OPTION
DEPLOY_OPTION=${DEPLOY_OPTION:-1}

if [ -z "$PROJECT_ID" ]; then
  read -p "Enter your GCP Project ID: " PROJECT_ID
  gcloud config set project "$PROJECT_ID"
fi

case $DEPLOY_OPTION in
  1)
    echo "--> Deploying to Google Cloud Run (Serverless Container)..."
    echo "Enabling Cloud Run & Cloud Build APIs if needed..."
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project="$PROJECT_ID"
    
    echo "Building and deploying service '$SERVICE_NAME' in region '$REGION'..."
    gcloud run deploy "$SERVICE_NAME" \
      --source . \
      --platform managed \
      --region "$REGION" \
      --allow-unauthenticated \
      --project "$PROJECT_ID"

    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format 'value(status.url)' --project "$PROJECT_ID")
    echo ""
    echo "=========================================================="
    echo " SUCCESS! Your website is live on Google Cloud Run:"
    echo " $SERVICE_URL"
    echo "=========================================================="
    echo ""
    echo "To map custom domains (americanlutheranchurchkellogg.com / alckellogg.com):"
    echo "gcloud beta run domain-mappings create --service $SERVICE_NAME --domain americanlutheranchurchkellogg.com --region $REGION"
    ;;

  2)
    echo "--> Deploying to Firebase Hosting (GCP Edge CDN)..."
    if ! command -v firebase &> /dev/null; then
      echo "Firebase CLI not found. Running with npx..."
      npx -y firebase-tools deploy --only hosting --project "$PROJECT_ID"
    else
      firebase deploy --only hosting --project "$PROJECT_ID"
    fi
    echo ""
    echo "=========================================================="
    echo " SUCCESS! Your website is deployed to Firebase Hosting on GCP."
    echo "=========================================================="
    ;;

  3)
    echo "--> Deploying to Google Cloud Storage Static Bucket..."
    BUCKET_NAME="americanlutheranchurchkellogg.com"
    read -p "Enter bucket name (Default: $BUCKET_NAME): " INPUT_BUCKET
    BUCKET_NAME=${INPUT_BUCKET:-$BUCKET_NAME}

    gsutil mb -p "$PROJECT_ID" -c standard -l "$REGION" -b on "gs://$BUCKET_NAME" || true
    gsutil web set -m index.html -e index.html "gs://$BUCKET_NAME"
    gsutil -m rsync -r -d . "gs://$BUCKET_NAME"
    gsutil iam ch allUsers:objectViewer "gs://$BUCKET_NAME"
    echo ""
    echo "=========================================================="
    echo " SUCCESS! Uploaded to gs://$BUCKET_NAME"
    echo " Web URL: https://storage.googleapis.com/$BUCKET_NAME/index.html"
    echo "=========================================================="
    ;;
esac
