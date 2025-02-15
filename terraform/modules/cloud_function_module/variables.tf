variable "gcp_project" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
}

variable "gcp_bucket" {
  description = "BigQuery bucket Name"
  type        = string
}

variable "function_name" {
  description = "Name of the Cloud Function"
  type        = string
}

variable "function_entry_point" {
  description = "Entry point of the Cloud Function"
  type        = string
}

variable "runtime" {
  description = "Runtime for the Cloud Function"
  type        = string
  default     = "python310"
}

variable "apis_enabled" {
  description = "List of dependencies to ensure APIs are enabled"
  type        = list(any)
  default     = []
}
