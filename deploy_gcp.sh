#!/bin/bash

if [ "$#" -lt 3 ]; then
   echo "Usage:  ./deploy_gcp.sh billingid project-prefix  email"
   echo "   eg:  ./deploy_gcp.sh 0X0X0X-0X0X0X-0X0X0X learnml-20170106  somebody@gmail.com someother@gmail.com"
   exit
fi

ACCOUNT_ID=$1
shift
PROJECT_PREFIX=$1
shift
EMAIL=$1

gcloud components update
gcloud components install alpha

PROJECT_ID=$(echo "${PROJECT_PREFIX}" | sed 's/@/x/g' | sed 's/\./x/g' | cut -c 1-30)
echo "Creating project $PROJECT_ID for $EMAIL ... "

# create
gcloud projects create $PROJECT_ID
sleep 2

# editor
rm -f iam.json.*
gcloud alpha projects get-iam-policy $PROJECT_ID --format=json > iam.json.orig
cat iam.json.orig | sed s'/"bindings": \[/"bindings": \[ \{"members": \["user:'$EMAIL'"\],"role": "roles\/editor"\},/g' > iam.json.new
gcloud alpha projects set-iam-policy $PROJECT_ID iam.json.new

# billing
gcloud alpha billing accounts projects link $PROJECT_ID --billing-account=$ACCOUNT_ID

#for SERVICE in "containerregistry" "container" "cloudbuild"; do
#  gcloud services enable ${SERVICE}.googleapis.com --project=${PROJECT_ID} --async
#  sleep 1
#done

# Create service account and generate key
SERVICE_ACCOUNT_NAME="terraform-sa-${PROJECT_PREFIX}"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --project=${PROJECT_ID} --display-name "Service Account for ${PROJECT_PREFIX}"

gcloud iam service-accounts keys create "${SERVICE_ACCOUNT_NAME}-key.json" --iam-account=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --project=${PROJECT_ID}

# Назначение всех необходимых ролей
ROLES=(
  "roles/editor"
  "roles/bigquery.admin"
  "roles/storage.admin"
  "roles/serviceusage.admin"
  "roles/cloudfunctions.admin"
  "roles/cloudbuild.builds.editor"
  "roles/artifactregistry.admin"
  "roles/viewer"
)

for role in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="${role}"
done

echo "Service account key saved to ${SERVICE_ACCOUNT_NAME}-key.json"

FOLDER_PATH=$(pwd)
ENV_FILE=".env"
SA_KEY_FILE="${FOLDER_PATH}/${SERVICE_ACCOUNT_NAME}-key.json"
PROJECT_VARS="/home/wudmc/PycharmProjects/prefect-tg/config/visionz.env"

echo "GOOGLE_APPLICATION_CREDENTIALS=${SA_KEY_FILE}" > $ENV_FILE
echo "GCP_PROJECT_ID=${PROJECT_ID}" >> $ENV_FILE
echo "VISIONZ_HOME=${FOLDER_PATH}" >> $ENV_FILE
echo "PROJECT_VARS=${PROJECT_VARS}" >> $ENV_FILE
echo ".env file updated with project credentials."