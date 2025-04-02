#!/bin/bash

if [ "$#" -lt 3 ]; then
   echo "Usage:  ./deploy_gcp_worker.sh [billing-id] project-prefix region email [--create]"
   echo "   eg:  ./deploy_gcp_worker.sh 0X0X0X-0X0X0X-0X0X0X myprefix europe-west1 someemail@gmail.com --create"
   echo "   or:  ./deploy_gcp_worker.sh myprefix europe-west1 someemail@gmail.com"
   exit 1
fi

SUFFIX="prefect"

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

WORKER_PROJECT_ID=$(echo "${PROJECT_PREFIX}" | sed 's/@/x/g' | sed 's/\./x/g' | cut -c 1-30)
echo "Creating $SUFFIX project $WORKER_PROJECT_ID for $EMAIL ... "

if [ "$CREATE_PROJECT" = true ]; then
    echo "Creating GCP project: $WORKER_PROJECT_ID"
    gcloud projects create $WORKER_PROJECT_ID
    # Wait for project to become ACTIVE
    echo "⏳ Waiting for project $WORKER_PROJECT_ID to become ACTIVE..."
    for i in {1..10}; do
      STATUS=$(gcloud projects describe "$WORKER_PROJECT_ID" --format="value(lifecycleState)")
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
    sleep 2
else
    echo "Using existing project: $WORKER_PROJECT_ID (no creation)"
fi

if ! gcloud config set project $WORKER_PROJECT_ID; then
    echo "❌ Failed to set GCP project. Make sure the project exists and you have access."
    exit 1
fi

gcloud auth application-default set-quota-project "$WORKER_PROJECT_ID"


gcloud config set run/region $REGION
gcloud config set compute/region $REGION

# editor
rm -f iam.json.*
gcloud alpha projects get-iam-policy $WORKER_PROJECT_ID --format=json > iam.json.orig
cat iam.json.orig | sed s'/"bindings": \[/"bindings": \[ \{"members": \["user:'$EMAIL'"\],"role": "roles\/editor"\},/g' > iam.json.new
gcloud alpha projects set-iam-policy $WORKER_PROJECT_ID iam.json.new

if [ "$CREATE_PROJECT" = true ]; then
    echo "Linking billing account..."
    gcloud billing projects link $WORKER_PROJECT_ID --billing-account=$ACCOUNT_ID
else
    echo "Skipping billing link (project assumed to already have billing set up)"
fi

ENV_FILE=".env"
PREFECT_WORK_POOL_NAME="${WORKER_PROJECT_ID}-gcp-worker"

echo "PREFECT_WORK_POOL_NAME=${PREFECT_WORK_POOL_NAME}" >> $ENV_FILE

echo ".env file updated with ${SUFFIX} project credentials."

echo "creating work pool in prefect for new gcp project"
#
BASE_TEMPLATE=$(prefect work-pool get-default-base-job-template -t cloud-run:push)
echo "$BASE_TEMPLATE" | sed "s/{{ region }}/$REGION/g" | sed "s/us-central1/$REGION/g"  > base-job-template.json

prefect work-pool create --type cloud-run:push --provision-infra --overwrite --base-job-template base-job-template.json "${PREFECT_WORK_POOL_NAME}"
