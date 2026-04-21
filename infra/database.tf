# ── Cloud SQL PostgreSQL 16 ─────────────────────────────────────────────────
resource "google_sql_database_instance" "main" {
  name             = "salon-lyol-pg"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-perf-optimized-N-2" # smallest current tier — upgrade to larger for production

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = true
      # No authorized_networks needed — Cloud SQL Python Connector uses IAM auth
    }

    insights_config {
      query_insights_enabled = false # enable in production for query profiling
    }
  }

  deletion_protection = false # set to true before going to production
  depends_on          = [google_project_service.apis]
}

resource "google_sql_database" "salon_lyol" {
  name     = "salon_lyol"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  name     = "salon"
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

# ── Secrets ─────────────────────────────────────────────────────────────────
resource "google_secret_manager_secret" "db_password" {
  secret_id = "salon-db-password"
  replication {
    auto {
    }
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "salon-secret-key"
  replication {
    auto {
    }
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secret_key.id
  secret_data = var.secret_key
}
