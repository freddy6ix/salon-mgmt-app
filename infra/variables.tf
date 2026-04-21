variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region (Toronto)"
  type        = string
  default     = "northamerica-northeast2"
}

variable "db_password" {
  description = "PostgreSQL password for the app database user"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "JWT signing secret — generate with: openssl rand -hex 32"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository for Workload Identity Federation, e.g. 'owner/repo'"
  type        = string
}
