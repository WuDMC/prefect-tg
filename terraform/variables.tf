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

variable "function_name" {
  description = "Name of the Cloud Function"
  type        = string
  default     = "msgs2bq"
}

variable "function_entry_point" {
  description = "Entry point for the Cloud Function"
  type        = string
  default = "gcs_to_bigquery"
}

variable "function_runtime" {
  description = "Runtime for the Cloud Function"
  type        = string
  default     = "python310"
}

variable "credentials" {
  description = "Path to GCP service account key file"
  type        = string
}