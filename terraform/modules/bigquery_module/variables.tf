variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
}

variable "bq_dataset" {
  description = "BigQuery Dataset Name"
  type        = string
}

variable "bq_table" {
  description = "BigQuery Table Name"
  type        = string
}
