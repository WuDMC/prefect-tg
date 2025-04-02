# 🚀 Telegram Parser Prefect Project

A full-stack data engineering pipeline on Google Cloud Platform (GCP) using Prefect, Terraform, and Cloud-native services.

## ✨ Overview

This project automates the end-to-end flow of collecting, processing, and storing Telegram messages using a clean and production-grade cloud architecture:

- **📦 Modular Telegram Parsing Logic**  
  All logic for scraping Telegram channels is packaged into a standalone Python module. It runs inside serverless Cloud Run containers, ensuring clean separation of responsibilities and reusable code.

- **⚙️ Orchestration with Prefect**  
  Prefect Cloud handles orchestration, triggering parsing jobs on schedule or on demand through registered flows and Cloud Run workers.

- **💾 Data Lake Layers on GCP**  
  Google Cloud Storage is used for raw data backups and intermediate message files. Parsed data is staged in BigQuery for further analytics, serving as the data lake layer.

- **🚀 Automated Infrastructure Deployment**  
  All components — from GCP projects to data pipelines — are deployed automatically using Terraform and bash scripts, making onboarding and replication effortless.

🛠️ Tech stack:
- Google Cloud (GCP): IAM, BigQuery, GCS, Pub/Sub, Cloud Functions, Cloud Run
- Prefect Cloud + Prefect Work Pools
- Terraform for infrastructure provisioning
- Python for orchestration and flows
- Bash scripts for deployment automation

📦 Architecture:
- A Prefect flow is deployed to Prefect Cloud
- It pushes jobs to a Cloud Run worker (GCP Worker Project)
- The worker parses messages and saves backups to a GCS bucket
- A Pub/Sub trigger on the bucket fires a Cloud Function
- The function writes parsed messages to BigQuery

## ⚙️ Requirements

- Python 3.10+
- Terraform (>= v1.3)
- gcloud CLI (authenticated)
- Prefect CLI (authenticated)
- Valid Google Cloud Billing Account
- A file with your project secrets/environment variables (see below)

## 📁 Step 0 — Create a project config file

Before deploying, create a file with all necessary environment variables, for example: `config/visionz.env`

Example contents:

```env
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/.../workspaces/...
PREFECT_WORKSPACE=<spacename>/default
PREFECT_API_KEY=<your-prefect-api-key>

TG_API_ID=<tg_api_id>
TG_API_HASH=<tg_api_hash>
SESSION_STRING='...'

GCS_BUCKET_NAME="tg_msgs" # use own uniq backet names
GCS_BACKUP_BUCKET_NAME="tg_msgs_backup" # use own uniq backet names
CHANNEL_METADATA_PATH="job_parser/channels.json" # path to store stats
MSGS_DATA_PATH="job_parser/msgs" # path to store NLD JSONS 

BIGQUERY_DATASET="tg" # dataset
BIGQUERY_RAW_MESSAGES_TABLE="messages_raw" # table

# setting for parser
START_DATE="2024-04-01"
MAX_LIMIT=50
ACCOUNT_NAME="prefect_gcp"
BLACK_LIST='["-1", "-2"]' # channel ids
WHITE_LIST=[]
```

## 🧪 Step-by-step deployment guide (example)

These are the typical steps for deploying this project from scratch:

0. **Install Terraform**
   Make sure you have [Terraform](https://developer.hashicorp.com/terraform/downloads) installed.

1. **Clone the repository and install dependencies**
   ```bash
   git clone https://github.com/WuDMC/prefect-tg.git
   cd prefect-tg
   make install
   ```

2. **Create a Telegram application to get API ID and API Hash**
   - Follow the steps here: https://core.telegram.org/api/obtaining_api_id
   - Create the app here: https://my.telegram.org/apps

3. **Generate your session string**
   Run the following command:
   ```bash
   python3 tg_login.py --api_id <your_api_id> --api_hash <your_api_hash>
   ```

4. **Get Telegram channel IDs to parse**
   - Use the bot [@getidsbot](https://t.me/getidsbot) to retrieve channel IDs.
   - Add them to the `.env` file like:
     ```env
     WHITE_LIST='["-1001776649308", "-1001432211209", "-1001865511874", "-1001335735566"]'
     ```

5. **Create an environment file**
   Example: `config/spain_news.env`  
   It should contain all the necessary variables (see earlier section for full example).

6. **Run the interactive deployment script**
   ```bash
   bash deploy_all.sh
   ```

   It will print out step-by-step deployment commands after setup.

7. **Manually deploy GCP infrastructure (if needed)**
   Example:
   ```bash
   bash deploy_gcp_dwh.sh <project-id> europe-west1 your@email.com --create <billing-id>
   python3 terraform_deploy.py

   bash deploy_gcp_worker.sh <project-id> europe-west1 your@email.com
   ```

8. **Deploy Prefect flows**
   ```bash
   PYTHONPATH=$(pwd) python3 flows/check_dialogs.py
   PYTHONPATH=$(pwd) python3 flows/parse_msgs.py
   ```

9. **Run the check_dialogs flow once manually**
   This initializes the metadata/statistics for further parsing.

## 🔁 Step 2 — Re-run parts manually (optional)

After initial deploy, you can re-run any part with:

```bash
# Deploy DWH infra
bash deploy_gcp_dwh.sh PROJECT_PREFIX REGION EMAIL --create BILLING_ID
python3 terraform_deploy.py

# Deploy Worker
bash deploy_gcp_worker.sh  PROJECT_PREFIX REGION EMAIL --create BILLING_ID

# Deploy Prefect flows (must be run from project dir)
python3 flows/check_dialogs.py
python3 flows/parse_msgs.py
```

The script will print exact commands after the interactive setup.

## 📊 Output

Once deployed:
- Telegram messages are backed up to GCS
- Pub/Sub triggers Cloud Function to write to BigQuery
- You can track job execution in Prefect Cloud

## ✅ Why this project is cool

- Combines **IaC**, **Prefect orchestration**, **event-driven GCP**, and **data engineering** principles
- Fully automated from zero to production
- Scalable, reproducible, and modular

Perfect for showcasing:
- Cloud infra knowledge
- Prefect work pool orchestration
- BigQuery ingestion pipelines
- Real-world ETL/ELT scenarios
