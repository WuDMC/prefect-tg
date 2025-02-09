variable "gcp_project" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "bq_dataset" {
  description = "BigQuery dataset name"
  type        = string
  default     = "example_dataset"
}

variable "bq_table" {
  description = "BigQuery table name"
  type        = string
  default     = "example_table"
}
variable "function_name" {
  description = "Name of the Cloud Function"
  type        = string
}

variable "function_entry_point" {
  description = "Entry point for the Cloud Function"
  type        = string
}

variable "function_runtime" {
  description = "Runtime for the Cloud Function"
  type        = string
  default     = "python310"
}
