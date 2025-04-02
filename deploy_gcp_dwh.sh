#!/bin/bash

if [ "$#" -lt 3 ]; then
   echo "Usage:  ./deploy_gcp_dwh.sh billingid project-prefix region email"
   echo "   eg:  ./deploy_gcp_dwh.sh 0X0X0X-0X0X0X-0X0X0X learnml-20170106  europe-west1 someother@gmail.com"
   exit
fi

SUFFIX="dwh"

PROJECT_PREFIX=$1
REGION=$2
EMAIL=$3

CREATE_PROJECT=false
if [[ "$4" == "--create" ]]; then
  CREATE_PROJECT=true
  ACCOUNT_ID=$5
fi

gcloud components update
gcloud components install alpha

DWH_PROJECT_ID=$(echo "${PROJECT_PREFIX}" | sed 's/@/x/g' | sed 's/\./x/g' | cut -c 1-30)
echo "Creating $SUFFIX project $DWH_PROJECT_ID for $EMAIL ... "

if [ "$CREATE_PROJECT" = true ]; then
  echo "Creating GCP project: $DWH_PROJECT_ID"
  gcloud projects create $DWH_PROJECT_ID
  # Wait for project to become ACTIVE
  echo "⏳ Waiting for project $DWH_PROJECT_ID to become ACTIVE..."
  for i in {1..10}; do
    STATUS=$(gcloud projects describe "$DWH_PROJECT_ID" --format="value(lifecycleState)")
    echo "   Project state: $STATUS"
    if [[ "$STATUS" == "ACTIVE" ]]; then
      break
    fi
    sleep 3
  done

  if [[ "$STATUS" != "ACTIVE" ]]; then
    echo "❌ Project did not become ACTIVE in time."
    exit 1
  fi
else
  echo "Using existing project: $DWH_PROJECT_ID (no creation)"
fi

if ! gcloud projects describe "$DWH_PROJECT_ID" &>/dev/null; then
  echo "❌ Project $DWH_PROJECT_ID does not exist or is inaccessible. Aborting."
  exit 1
fi

if ! gcloud config set project $DWH_PROJECT_ID; then
  echo "❌ Failed to set GCP project. Make sure the project exists and you have access."
  exit 1
fi

gcloud auth application-default set-quota-project "$DWH_PROJECT_ID"

#gcloud compute project-info add-metadata \
#    --metadata google-compute-default-region=$REGION,google-compute-default-zone=$REGION

gcloud config set run/region $REGION
gcloud config set compute/region $REGION

# editor
rm -f iam.json.*
if ! gcloud alpha projects get-iam-policy "$DWH_PROJECT_ID" --format=json > iam.json.orig; then
  echo "❌ Failed to get IAM policy. Check project access."
  exit 1
fi
cat iam.json.orig | sed s'/"bindings": \[/"bindings": \[ \{"members": \["user:'$EMAIL'"\],"role": "roles\/editor"\},/g' > iam.json.new
gcloud alpha projects set-iam-policy $DWH_PROJECT_ID iam.json.new

if [ "$CREATE_PROJECT" = true ]; then
  echo "Linking billing account..."
  gcloud billing projects link $DWH_PROJECT_ID --billing-account=$ACCOUNT_ID
else
  echo "Skipping billing link (project assumed to already have billing set up)"
fi

#for SERVICE in "compute.googleapis.com" "container" "cloudbuild"; do
#  gcloud services enable ${SERVICE}.googleapis.com --project=${DWH_PROJECT_ID} --async
#  sleep 1
#done

# Create service account and generate key
SERVICE_ACCOUNT_NAME=$(echo "terra-${PROJECT_PREFIX}" | sed 's/@/x/g' | sed 's/\./x/g' | cut -c 1-30)
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --project=${DWH_PROJECT_ID} --display-name "Service Account for ${DWH_PROJECT_ID}"

gcloud iam service-accounts keys create "${SERVICE_ACCOUNT_NAME}-key.json" --iam-account=${SERVICE_ACCOUNT_NAME}@${DWH_PROJECT_ID}.iam.gserviceaccount.com --project=${DWH_PROJECT_ID}

if [ ! -f "${SERVICE_ACCOUNT_NAME}-key.json" ]; then
  echo "❌ Failed to create service account key."
  exit 1
fi

# Назначение всех необходимых ролей
assign_roles_safe() {
  local project_id="$1"
  local service_account="$2"
  shift 2
  local roles=("$@")

  for role in "${roles[@]}"; do
    echo "🔐 Assigning role: $role to $service_account@$project_id"

    local success=false
    for attempt in {1..3}; do
      if gcloud projects add-iam-policy-binding "$project_id" \
        --member="serviceAccount:${service_account}@${project_id}.iam.gserviceaccount.com" \
        --role="$role"; then
        echo "✅ Role $role assigned successfully"
        success=true
        break
      else
        echo "⚠️ Failed to assign $role (attempt $attempt), retrying in 2s..."
        sleep 2
      fi
    done

    if [ "$success" = false ]; then
      echo "❌ Failed to assign role $role after 3 attempts."
    fi

    sleep 1
  done
}

ROLES=(
  "roles/run.admin"
  "roles/iam.serviceAccountUser"
  "roles/editor"
  "roles/bigquery.admin"
  "roles/storage.admin"
  "roles/cloudfunctions.admin"
  "roles/cloudbuild.builds.editor"
  "roles/artifactregistry.admin"
  "roles/artifactregistry.reader"
  "roles/owner" # need to change to role who can create service accounts
  "roles/serviceusage.serviceUsageAdmin"  # Содержит serviceusage.services.enable
  "roles/iam.serviceAccountAdmin"  # Содержит iam.serviceAccounts.create
  "roles/iam.serviceAccountKeyAdmin"
)

assign_roles_safe "$DWH_PROJECT_ID" "$SERVICE_ACCOUNT_NAME" "${ROLES[@]}"

echo "Service account key saved to ${SERVICE_ACCOUNT_NAME}-key.json"

FOLDER_PATH=$(pwd)
ENV_FILE=".env"
SA_KEY_FILE="${FOLDER_PATH}/${SERVICE_ACCOUNT_NAME}-key.json"

#for terraform to create dwh project
echo "GOOGLE_APPLICATION_CREDENTIALS=${SA_KEY_FILE}" >> $ENV_FILE
echo "SERVICE_ACCOUNT=${SERVICE_ACCOUNT_NAME}@${DWH_PROJECT_ID}.iam.gserviceaccount.com" >> $ENV_FILE

echo ".env file updated with ${SUFFIX} project credentials."

# run terraform here as well