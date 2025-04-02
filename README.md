# 🚀 Telegram Parser Prefect Project

A full-stack data engineering pipeline on Google Cloud Platform (GCP) using Prefect, Terraform, and Cloud-native services.

## ✨ Overview

This project automates the collection, parsing, and storage of Telegram channel messages into Google Cloud — leveraging the best of Prefect orchestration, Cloud Run workers, BigQuery analytics, and Pub/Sub triggers.

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

## 🪄 Step 1 — Run the interactive deployment

```bash
bash deploy_all.sh
```

This script will:
- Ask for region, email, and billing account (if needed)
- Optionally create 1 or 2 GCP projects
- Deploy Terraform infrastructure to the DWH project
- Set up a Prefect Cloud Run Push Work Pool in the Worker project
- Deploy 2 Prefect flows

A `.env` file will be generated automatically for local re-use.

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

---


сюда запишу что я делал для создания проект
0 - инсталл террафрм
1 - гит клоне  и make install
2 - создаю апп в тг and get api id and api hash

https://core.telegram.org/api/obtaining_api_id 
https://my.telegram.org/apps

3 - получиаю сешн стринг
 python3 tg_login.py --api_id xxx  --api_hash yyy
4 - с помощью бота @getidsbot получаю айдишники каналов для парсинга
и сохраняю в виду
WHITE_LIST='["-1001776649308", "-1001432211209", "-1001865511874", "-1001335735566"]'
5 создал енв файл с проектом config/spain_news.env
6 деплой алл и получаю команды для деплоя по шагам
7 - деплой гугл проект
/bin/bash ./deploy_gcp_dwh.sh tg-es-news europe-west1 mr.quan4i@gmail.com --create 014A87-412A23-73F5E4
python3 terraform_deploy.py
/bin/bash ./deploy_gcp_worker.sh tg-es-news europe-west1 mr.quan4i@gmail.com
PYTHONPATH=$(pwd) python3 flows/check_dialogs.py
PYTHONPATH=$(pwd) python3 flows/parse_msg.py
