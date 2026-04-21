output "api_url" {
  description = "Cloud Run API service URL — set as API_URL in GitHub Actions variables"
  value       = google_cloud_run_v2_service.api.uri
}

output "frontend_url" {
  description = "Cloud Run frontend service URL"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "artifact_registry" {
  description = "Artifact Registry prefix for Docker push, e.g. docker push <this>/salon-api:tag"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/salon-mgmt"
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name (project:region:instance)"
  value       = google_sql_database_instance.main.connection_name
}

output "workload_identity_provider" {
  description = "WIF provider — set as GCP_WORKLOAD_IDENTITY_PROVIDER in GitHub Actions variables"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "deployer_service_account" {
  description = "Deployer SA email — set as GCP_SERVICE_ACCOUNT in GitHub Actions variables"
  value       = google_service_account.deployer.email
}
