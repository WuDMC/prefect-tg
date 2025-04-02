#!/bin/bash

ask_yes_no() {
  local question=$1
  local default=$2
  local answer
  read -p "$question [y/n] (default: $default): " answer
  answer=${answer:-$default}
  [[ "$answer" =~ ^[Yy]$ ]] && return 0 || return 1
}

ask_input() {
  local question=$1
  local default=$2
  local answer
  read -p "$question (default: $default): " answer
  echo "${answer:-$default}"
}

clear

echo "🚀 Interactive GCP Deployment Setup"

REGION=$(ask_input "Enter the GCP region" "europe-west1")
EMAIL=$(ask_input "Enter your email for IAM access" "")
PROJECT_VARS_PATH=$(ask_input "Enter the relative path to your PROJECT_VARS file" "config/visionz.env")
WORKER_ACCOUNT_ID=""
CREATE_WORKER_PROJECT=true

# --- DWH SETUP ---
echo -e "\n📦 Data Warehouse Setup"
SEPARATE_PROJECTS=false
CREATE_DHW_PROJECT=true
if ask_yes_no "Do you already have a GCP project for DWH?" "n"; then
  DWH_PROJECT=$(ask_input "Enter your existing GCP Project ID for DWH" "")
  CREATE_DHW_PROJECT=false
  if ask_yes_no "Do you want to provision infrastructure in this project via Terraform?" "y"; then
    RUN_TERRAFORM=true
  else
    RUN_TERRAFORM=false
  fi
else
  PREFIX=$(ask_input "Enter a project name prefix (e.g. myteam-dev)" "myteam-dev")
  DWH_PROJECT="$PREFIX"
  RUN_TERRAFORM=true
  DWH_ACCOUNT_ID=$(ask_input "Enter the Billing Account ID for DWH project" "")
fi

# --- WORKER SETUP ---
echo -e "\n🧱 Prefect Worker Setup"
if ask_yes_no "Do you want to use the same project for Prefect Worker?" "y"; then
  WORKER_PROJECT=$DWH_PROJECT
  CREATE_WORKER_PROJECT=false
  WORKER_ACCOUNT_ID=$DWH_ACCOUNT_ID
  SETUP_PREFECT=true
else
  SEPARATE_PROJECTS=true
  if ask_yes_no "Do you already have a separate GCP project for Prefect Worker?" "n"; then
    WORKER_PROJECT=$(ask_input "Enter your existing GCP Project ID for Prefect Worker" "")
    CREATE_WORKER_PROJECT=false
    if ask_yes_no "Do you want to provision worker infrastructure in this project?" "y"; then
      SETUP_PREFECT=true
    else
      SETUP_PREFECT=false
    fi
  else
    PREFIX=$(ask_input "Enter a project name prefix (e.g. myteam-dev)" "myteam-dev")
    WORKER_PROJECT="${PREFIX}-prefect"
    CREATE_WORKER_PROJECT=true
    WORKER_ACCOUNT_ID=$(ask_input "Enter the Billing Account ID for Worker project" "")
    SETUP_PREFECT=true
    DWH_PROJECT="${PREFIX}-dwh"  # Add suffix to DWH if projects are separate
  fi
fi

# --- Summary ---
mask_billing_id() {
  local id=$1
  echo "${id:0:3}***-***${id:14:6}"
}

echo -e "\n🧾 Summary:"
echo "📦 Data Warehouse (DWH):"
echo "  - DWH Project:           $DWH_PROJECT"
echo "  - Create DWH Project:    $CREATE_DHW_PROJECT"
echo "  - Run Terraform:         $RUN_TERRAFORM"
if [ -n "$DWH_ACCOUNT_ID" ]; then
  echo "  - DWH Billing Account:   $(mask_billing_id $DWH_ACCOUNT_ID)"
fi
echo
echo "🧱 Prefect Worker:"
echo "  - Prefect Project:       $WORKER_PROJECT"
echo "  - Create Worker Project: $CREATE_WORKER_PROJECT"
echo "  - Setup Prefect Pool:    $SETUP_PREFECT"
if [ -n "$WORKER_ACCOUNT_ID" ]; then
  echo "  - Worker Billing Acc.:   $(mask_billing_id $WORKER_ACCOUNT_ID)"
fi
echo
echo "🌍 Common:"
echo "  - Region:                $REGION"
echo "  - Email:                 $EMAIL"

echo
if ! ask_yes_no "Proceed with deployment?" "y"; then
  echo -e "\nAborted by user."
  exit 1
fi

# --- Execution ---
echo -e "\n🚀 Starting deployment..."
# --- Generating .env file ---
FOLDER_PATH=$(pwd)
ENV_FILE=".env"

echo "DWH_PROJECT_ID=${DWH_PROJECT}" >> $ENV_FILE
echo "WORKER_PROJECT_ID=${WORKER_PROJECT}" >> $ENV_FILE
echo "REGION=${REGION}" >> $ENV_FILE
echo "VISIONZ_HOME=${FOLDER_PATH}" >> $ENV_FILE
echo "PROJECT_VARS=${FOLDER_PATH}/${PROJECT_VARS_PATH}" >> $ENV_FILE

echo -e "\\n🔁 To re-run deployments manually without virtualenv:"
if [ "$CREATE_DHW_PROJECT" = true ]; then
  echo "/bin/bash ./deploy_gcp_dwh.sh $DWH_PROJECT $REGION $EMAIL --create $DWH_ACCOUNT_ID"
else
  echo "/bin/bash ./deploy_gcp_dwh.sh $DWH_PROJECT $REGION $EMAIL"
fi

echo "python3 terraform_deploy.py"

if [ "$CREATE_WORKER_PROJECT" = true ]; then
  echo "/bin/bash ./deploy_gcp_worker.sh $WORKER_PROJECT $REGION $EMAIL --create $WORKER_ACCOUNT_ID"
else
  echo "/bin/bash ./deploy_gcp_worker.sh $WORKER_PROJECT $REGION $EMAIL"
fi

echo "python3 flows/check_dialogs.py"
echo "python3 flows/parse_msg.py"


echo -e "\n✅ Deployment completed."

# --- Deploying Flows ---
echo -e "\n🚚 Deploying Prefect flows..."

#python3 flows/check_dialogs.py
#python3 flows/parse_msgs.py

echo -e "\n✅ All flows deployed."
