# Prefect Project

/bin/bash /home/wudmc/PycharmProjects/prefect-tg/deploy_gcp.sh 013763-76D7A4-EBF34A tg-sp-ai-dev mr.quan4i@gmail.com

sudo apt update && sudo apt install google-cloud-sdk
gcloud components update
gcloud auth configure-docker

deactivate venv