# ── Briefing output bucket ───────────────────────────────────────────────────
resource "google_storage_bucket" "briefings" {
  name          = "${var.project_id}-briefings"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "cloud_run_briefings_writer" {
  bucket = google_storage_bucket.briefings.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run.email}"
}
