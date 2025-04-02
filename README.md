# 🚀 VISIONZ

This project automates the end-to-end flow of collecting, processing, and storing Telegram messages using a clean and production-grade cloud architecture:

## ✨ Overview

- **📦 Modular Telegram Parsing Logic**  
  All logic for scraping Telegram channels is packaged into a standalone Python module. It runs inside serverless Cloud Run containers, ensuring clean separation of responsibilities and reusable code.

- **⚙️ Orchestration with Prefect**  
  Prefect Cloud handles orchestration, triggering parsing jobs on schedule or on demand through registered flows and Cloud Run workers.

- **💾 Lakehouse Architecture on GCP**  
  Raw data is stored in Google Cloud Storage as a landing zone for backups and intermediate message files. Parsed and structured data is then loaded into BigQuery, forming a lakehouse architecture that enables fast, scalable analytics on top of cloud-native storage.

- **🚀 Automated Infrastructure Deployment**  
  All components — from GCP projects to data pipelines — are deployed automatically using Terraform and bash scripts, making onboarding and replication effortless.

## ⚙️ Requirements

- Python 3.10+
- Terraform (>= v1.3)
- gcloud CLI (authenticated)
- Prefect CLI (authenticated)
- Valid Google Cloud Billing Account
- A file with your project secrets/environment variables (see below)

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
   Example: `config/project_vars.env`  
   It should contain all the necessary variables (see earlier section for full example).
   Example contents:

    ```env
    PREFECT_API_URL=https://api.prefect.cloud/api/accounts/.../workspaces/...
    PREFECT_WORKSPACE=<spacename>/default
    PREFECT_API_KEY=<your-prefect-api-key>
    
    SESSION_STRING='...' # from telegram 
    
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
    WHITE_LIST=[] # if not set will parse all channels
    ```

7. **Run the interactive deployment script**
   ```bash
   bash deploy_all.sh
   ```

   It will print out step-by-step deployment commands after setup.

8. **Manually deploy GCP infrastructure (if needed)**
   Example:
   ```bash
   bash deploy_gcp_dwh.sh <project-id> europe-west1 your@email.com --create <billing-id>
   python3 terraform_deploy.py
   bash deploy_gcp_worker.sh <project-id> europe-west1 your@email.com
   ```

9. **Deploy Prefect flows**
   ```bash
   PYTHONPATH=$(pwd) python3 flows/check_dialogs.py
   PYTHONPATH=$(pwd) python3 flows/parse_msgs.py
   ```

10. **Run the check_dialogs flow once manually**
   This initializes the metadata/statistics for further parsing.


