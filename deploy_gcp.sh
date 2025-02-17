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
REGION=$1
shift
EMAIL=$1

gcloud components update
gcloud components install alpha

PROJECT_ID=$(echo "${PROJECT_PREFIX}" | sed 's/@/x/g' | sed 's/\./x/g' | cut -c 1-30)
echo "Creating project $PROJECT_ID for $EMAIL ... "

# create
gcloud projects create $PROJECT_ID
sleep 2

gcloud config set project $PROJECT_ID

gcloud compute project-info add-metadata \
    --metadata google-compute-default-region=$REGION,google-compute-default-zone=$REGION

gcloud config set run/region $REGION
gcloud config set compute/region $REGION

# editor
rm -f iam.json.*
gcloud alpha projects get-iam-policy $PROJECT_ID --format=json > iam.json.orig
cat iam.json.orig | sed s'/"bindings": \[/"bindings": \[ \{"members": \["user:'$EMAIL'"\],"role": "roles\/editor"\},/g' > iam.json.new
gcloud alpha projects set-iam-policy $PROJECT_ID iam.json.new

# billing
gcloud billing projects link $PROJECT_ID --billing-account=$ACCOUNT_ID


#for SERVICE in "compute.googleapis.com" "container" "cloudbuild"; do
#  gcloud services enable ${SERVICE}.googleapis.com --project=${PROJECT_ID} --async
#  sleep 1
#done

# Create service account and generate key
SERVICE_ACCOUNT_NAME="terraform-sa-${PROJECT_PREFIX}-dev"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --project=${PROJECT_ID} --display-name "Service Account for ${PROJECT_PREFIX}"

gcloud iam service-accounts keys create "${SERVICE_ACCOUNT_NAME}-key.json" --iam-account=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --project=${PROJECT_ID}

# Назначение всех необходимых ролей
ROLES=(
  "roles/run.admin"
  "roles/iam.serviceAccountUser"
  "roles/editor"
  "roles/bigquery.admin"
  "roles/storage.admin"
  "roles/serviceusage.admin"
  "roles/cloudfunctions.admin"
  "roles/cloudbuild.builds.editor"
  "roles/artifactregistry.admin"
  "roles/owner" # need to change to role who can create service accounts
  "roles/serviceusage.serviceUsageAdmin"  # Содержит serviceusage.services.enable
  "roles/iam.serviceAccountAdmin"  # Содержит iam.serviceAccounts.create
  "roles/iam.serviceAccountKeyAdmin"
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
PROJECT_VARS="${FOLDER_PATH}/config/visionz.env"
PREFECT_WORK_POOL_NAME="${PROJECT_ID}-gcp-worker"

echo "GOOGLE_APPLICATION_CREDENTIALS=${SA_KEY_FILE}" > $ENV_FILE
# shellcheck disable=SC2129
echo "SERVICE_ACCOUNT=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" >> $ENV_FILE
echo "GCP_PROJECT_ID=${PROJECT_ID}" >> $ENV_FILE
echo "GCP_REGION=${REGION}" >> $ENV_FILE
echo "VISIONZ_HOME=${FOLDER_PATH}" >> $ENV_FILE
echo "PROJECT_VARS=${PROJECT_VARS}" >> $ENV_FILE
echo "PREFECT_WORK_POOL_NAME=${PREFECT_WORK_POOL_NAME}" >> $ENV_FILE

echo ".env file updated with project credentials."

echo "creating work pool in prefect for new gcp project"

BASE_TEMPLATE=$(prefect work-pool get-default-base-job-template -t cloud-run:push)
echo "$BASE_TEMPLATE" | sed "s/{{ region }}/$REGION/g" | sed "s/us-central1/$REGION/g"  > base-job-template.json

prefect work-pool create --type cloud-run:push --provision-infra --overwrite --base-job-template base-job-template.json "${PREFECT_WORK_POOL_NAME}"



