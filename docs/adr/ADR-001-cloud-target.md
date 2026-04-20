# ADR-001: Cloud Target — Google Cloud Platform (GCP)

**Date:** 2026-04-20
**Status:** Accepted
**Deciders:** Frederick Ferguson

---

## Context

The system requires a cloud deployment for staging (Phase 1) and production (Phase 1+). The owner has hands-on experience with both GCP and Azure. A single cloud target must be chosen for Phase 1 to avoid split infrastructure and tooling overhead for a solo developer.

Requirements:
- Managed PostgreSQL (ADR-003)
- Container-based deployment (FastAPI backend + React static frontend)
- Object storage (provider/client photos, frontend static build)
- Secrets management (database credentials, API keys, SIN encryption key)
- Minimal operational overhead for a solo developer
- Path to multi-tenant production in Phase 3

---

## Decision

**Google Cloud Platform (GCP).**

---

## Rationale

Both GCP and Azure meet all requirements. GCP is chosen based on owner preference and familiarity.

### Service mapping

| Need | GCP service |
|------|-------------|
| Managed PostgreSQL | Cloud SQL (PostgreSQL 16) |
| Container deployment | Cloud Run |
| Static frontend hosting | Cloud Storage + Cloud CDN |
| Secrets management | Secret Manager |
| Container registry | Artifact Registry |
| CI/CD | Cloud Build (or GitHub Actions → Cloud Run) |
| DNS / load balancing | Cloud Domains + Cloud Load Balancing |
| Object storage (photos) | Cloud Storage |

### Why Cloud Run over GKE

Cloud Run (serverless containers) is the right fit for Phase 1:
- No cluster management overhead
- Scales to zero when unused (cost-effective for a staging environment with low traffic)
- Deploy by pushing a container image — no Kubernetes manifests required
- Straightforward path to higher scale in Phase 3 if needed (or migrate to GKE then)

GKE would be appropriate in Phase 3+ if multi-tenant traffic requires more control over networking, resource isolation, or custom autoscaling.

### Why Cloud SQL over self-managed Postgres

Cloud SQL provides automated backups, point-in-time recovery, and failover replicas without manual DBA work. For a solo developer, this is the correct trade-off. The connection string is stored in Secret Manager and injected via environment variable per 12-factor config.

---

## Consequences

- **Positive:** Single cloud to learn, bill, and operate. No split tooling.
- **Positive:** Cloud Run's scale-to-zero keeps staging costs near zero when idle.
- **Positive:** Secret Manager integrates cleanly with Cloud Run (secrets mounted as environment variables at deploy time).
- **Positive:** Cloud SQL's IAM authentication can replace password-based DB access in Phase 2 for improved security posture.
- **Negative:** Vendor lock-in to GCP-specific services. Mitigated by 12-factor config (no hardcoded GCP SDK calls in application code; infrastructure concerns stay in `infra/`).
- **Neutral:** Terraform used for all GCP resource provisioning (see IaC convention in CLAUDE.md). GCP provider for Terraform is mature.

---

## Initial GCP Project Structure

```
Project: salon-lyol-dev     (staging — Phase 1)
Project: salon-lyol-prod    (production — Phase 1 launch)
```

Separate projects provide billing isolation and IAM boundary between staging and production. Both use the same Terraform modules with different variable files.

---

## Staging Deployment Target (Phase 1)

| Component | Service | Notes |
|-----------|---------|-------|
| API | Cloud Run (single revision) | Deploy on every merge to main |
| Database | Cloud SQL db-f1-micro | Cheapest tier; upgrade at Phase 1 launch |
| Frontend | Cloud Storage bucket + CDN | Static Vite build |
| Secrets | Secret Manager | DB password, JWT secret, SIN encryption key |
| Container images | Artifact Registry | `gcr.io` replacement |
