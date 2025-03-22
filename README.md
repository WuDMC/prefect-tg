# Prefect Project

/bin/bash /home/wudmc/PycharmProjects/prefect-tg/deploy_gcp.sh REMOVED tg-sp-ai-dev REMOVED_EMAIL

sudo apt update && sudo apt install google-cloud-sdk
gcloud components update
gcloud auth configure-docker

deactivate venv