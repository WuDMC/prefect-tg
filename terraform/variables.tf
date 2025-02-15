variable "gcp_project" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
}

variable "bq_dataset" {
  description = "BigQuery dataset name"
  type        = string
}

variable "bq_table" {
  description = "BigQuery table name"
  type        = string
}

variable "gcp_bucket" {
  description = "BigQuery Dataset Name"
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

variable "credentials" {
  description = "Path to GCP service account key file"
  type        = string
}