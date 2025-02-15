variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
}

variable "gcp_bucket" {
  description = "BigQuery bucket Name"
  type        = string
}

variable "force_destroy" {
  description = "If true, allows bucket deletion even if it contains objects"
  type        = bool
  default     = true
}

variable "storage_class" {
  description = "Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)"
  type        = string
  default     = "STANDARD"
}
