variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "api_list" {
  description = "List of APIs to enable"
  type        = list(string)
}
