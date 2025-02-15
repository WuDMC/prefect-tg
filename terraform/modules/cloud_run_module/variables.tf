
variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
}

variable "prefect_api_url" {
  description = "Prefect api url"
  type        = string
}
variable "prefect_api_key" {
  description = "Prefect api key"
  type        = string
}

variable "prefect_work_pool" {
  description = "Prefect work pool name"
  type        = string
}
variable "service_account" {
  description = "gcp service account name"
  type        = string
}
#gcloud run deploy prefect-worker --image=prefecthq/prefect:3-latest \
#--set-env-vars PREFECT_API_URL=$PREFECT_API_URL,PREFECT_API_KEY=$PREFECT_API_KEY \
#--service-account <YOUR-SERVICE-ACCOUNT-NAME> \
#--no-cpu-throttling \
#--min-instances 1 \
#--startup-probe httpGet.port=8080,httpGet.path=/health,initialDelaySeconds=100,periodSeconds=20,timeoutSeconds=20 \
#--args "prefect","worker","start","--install-policy","always","--with-healthcheck","-p","<WORK-POOL-NAME>","-t","cloud-run"