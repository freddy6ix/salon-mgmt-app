# Go-Live Checklist — Salon Lyol Production Tenant

> This document tracks everything that must be done before the PROD tenant handles real client data.
> It is separate from the feature backlog (`docs/backlog.md`).
> See `docs/adr/ADR-005-production-tenant-isolation.md` for the architectural rationale.

---

## Status legend
- `[ ]` Not started
- `[~]` In progress
- `[x]` Done

---

## 1. Database — Security hardening

- `[ ]` **Implement PostgreSQL Row Level Security (RLS)**
  Enable RLS on all tenant-scoped tables. Application DB role enforces `tenant_id = current_setting('app.current_tenant_id')::uuid` on every SELECT/INSERT/UPDATE/DELETE. Superuser/migration role bypasses RLS (intentional).
  _Tracked as a code task — see Section 6 below._

- `[ ]` **Enforce SSL connections on Cloud SQL**
  In the Cloud SQL console: edit the instance → Connections → SSL mode → **Require SSL**. Plain-text connections will be rejected.

- `[ ]` **Enable Cloud SQL audit logging**
  In GCP Console → Cloud SQL → your instance → Operations → Logs → enable **Data Access** audit logs (DATA_READ, DATA_WRITE). Also enable **Cloud Audit Logs** at the project level for Cloud SQL Admin activity.

- `[ ]` **Verify Cloud SQL Auth Proxy is the only connection path**
  Confirm no authorised networks are listed on the Cloud SQL instance (Cloud Run connects via Unix socket / Auth Proxy only). Remove any IP-based authorised networks if present.

---

## 2. Application — Code tasks before go-live

- `[ ]` **Implement RLS in a migration**
  See Section 6 for the implementation plan.

- `[ ]` **Harden API: confirm no endpoint returns cross-tenant data**
  Manual audit: check every router for queries that join across tenant boundaries without a `tenant_id` filter. Particular attention to public endpoints (`/public/*`), appointment book queries, and any aggregate/report queries.

- `[ ]` **Ensure seed script does NOT run in production container**
  The seed was added to `docker-entrypoint.sh` for staging convenience. Before a production deployment, gate it on an env var (`SEED=true`) so it only runs on staging.
  _See Section 6 for the code change._

---

## 3. PROD tenant — Setup

- `[ ]` **Create PROD tenant via admin API or direct seed**
  Use a distinct slug (e.g. `salon-lyol-prod`) and name ("Salon Lyol"). Record the tenant UUID.

- `[ ]` **Create PROD admin user with a strong password**
  Do NOT use `changeme123`. Use a password manager to generate a strong credential. This becomes the owner login for live operations.

- `[ ]` **Set branding, contact details, operating hours for PROD tenant**
  Via Settings in the app — these propagate to emails, the landing page, and appointment grid.

- `[ ]` **Seed service catalog and provider prices for PROD tenant**
  Run the seed against the PROD tenant (or enter manually via the Services page). This is the real catalog, not test data.

- `[ ]` **Import client data from existing system (P2-20)**
  Once P2-20 (bulk import) is shipped, use it to migrate existing client history.

---

## 4. Operational readiness

- `[ ]` **Separate staff accounts for PROD**
  All live staff have their own PROD accounts. No shared logins between dev and prod tenants.

- `[ ]` **Dev/test tenant clearly labelled**
  Rename the dev tenant (e.g. slug `salon-lyol-dev`, name "Salon Lyol [DEV]") so it is obvious which tenant you are logged into.

- `[ ]` **Backup policy reviewed**
  Cloud SQL automated backups: verify retention period is set appropriately (minimum 7 days recommended for a live salon). Confirm point-in-time recovery (PITR) is enabled on the Cloud SQL instance.

- `[ ]` **Cloud Run min instances set for PROD**
  Set `--min-instances=1` on the production Cloud Run services to eliminate cold-start latency for staff. (Staging can remain at 0.)

- `[ ]` **Custom domain for PROD** (optional at launch)
  Map `app.salonlyol.ca` to the Cloud Run frontend service if a custom domain is desired for the live app.

- `[ ]` **SMTP configured for PROD tenant**
  Under Settings → Email in the PROD tenant: configure live SMTP credentials (not the test account used in staging). Send a test email to verify.

- `[ ]` **Smoke test on PROD tenant before staff onboarding**
  Full end-to-end test: create an appointment, book a client, confirm, check out, send a receipt. Do this with a test client before real clients are in the system.

---

## 5. Go / No-go gate

All items in sections 1–4 must be `[x]` before real client data is entered.

---

## 6. Implementation tasks (tracked here, not in feature backlog)

### 6a — PostgreSQL RLS

Add a migration that:
1. Creates a restricted application DB role (`app_user`) if it doesn't already exist
2. Enables RLS on every tenant-scoped table (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`)
3. Creates a permissive policy: `CREATE POLICY tenant_isolation ON ... USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)`
4. Grants `app_user` access; migration role (owner) bypasses RLS

Update `app/database.py` to execute `SET app.current_tenant_id = '<uuid>'` at the start of each request session, derived from the authenticated user's tenant.

### 6b — Seed gate for production

Update `scripts/docker-entrypoint.sh`:
```sh
if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "Running seed..."
  PYTHONPATH=/app python scripts/seed.py
fi
```

Update the staging Cloud Run deploy in `deploy.yml` to pass `--update-env-vars RUN_SEED=true`. Production deploy leaves `RUN_SEED` unset (defaults to false).
