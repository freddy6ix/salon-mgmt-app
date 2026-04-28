# ADR-005 — Production Tenant Isolation Strategy

**Date:** 2026-04-28
**Status:** Accepted

---

## Context

The system is multi-tenant from day one — every tenant-scoped table carries a `tenant_id` column and all application queries include a `WHERE tenant_id = ?` clause enforced via `StaffUser`/`AdminUser` dependencies. The current deployment hosts a single dev/test tenant (Salon Lyol staging).

The next step is to introduce a second tenant for live production data — Salon Lyol production — in the **same GCP project, same Cloud Run services, and same Cloud SQL instance**. A separate GCP project was considered and rejected: it doubles infrastructure maintenance, breaks the single-deployment model, and adds no meaningful security benefit at this scale since the isolation goal is data separation, not blast-radius containment between environments.

The question is: what additional security layers sit underneath the application-level `tenant_id` filtering?

---

## Decision

**Two tenants in one database, hardened by four layers:**

### Layer 1 — Logical isolation (existing)
Every table has `tenant_id NOT NULL` with an index. Every application query filters by `tenant_id` via the authenticated user's tenant context. A staff user from Tenant A cannot reach Tenant B's rows through any API endpoint.

**Weakness:** relies entirely on application correctness. A query bug that omits the `WHERE tenant_id = ?` clause would leak data.

### Layer 2 — PostgreSQL Row Level Security (to be implemented before go-live)
RLS policies on all tenant-scoped tables enforce the tenant filter at the database engine level, independent of application code. Even if a query omits the tenant clause — through a bug, a raw query, a future migration script, or direct `psql` access with the application role — the DB returns only the rows the session's tenant is entitled to see.

Implementation: set a session variable (`app.current_tenant_id`) before each query; RLS policies check `tenant_id = current_setting('app.current_tenant_id')::uuid`. Applied to the application DB role only — the superuser/owner role (used only for migrations) bypasses RLS, which is intentional and appropriate.

### Layer 3 — Cloud SQL security (to be verified at go-live)
- **Encryption at rest:** on by default (Google-managed keys). Acceptable for this scale.
- **SSL/TLS enforcement:** Cloud SQL SSL mode set to `REQUIRE` — plain-text connections rejected at the DB level, not just discouraged.
- **Audit logging:** Cloud SQL audit logs enabled for data access and admin activity in the GCP project. These logs are immutable and captured outside the application.
- **Authorised networks:** Cloud SQL not exposed to the public internet; connections via Cloud SQL Auth Proxy only (already the case via Cloud Run sidecar).

### Layer 4 — PROD tenant credentials
- The PROD tenant admin account is created with a strong, individually set password — not the seed default `changeme123`.
- The dev/test tenant's admin accounts have no elevated privileges that would allow them to act as a different tenant; the application enforces tenant scoping at the auth layer.
- Separate staff user accounts for PROD — no shared logins between environments.

---

## Consequences

**Good:**
- Single deployment to maintain — code ships to one place, both tenants see it simultaneously.
- RLS turns a developer mistake into a zero-data-leak outcome rather than a breach.
- Cloud SQL audit logs give an immutable access record for the production tenant.
- No additional infrastructure cost beyond enabling existing Cloud SQL features.

**Accepted limitations:**
- Both tenants share the same Cloud SQL instance. A DB-level compromise (Cloud SQL credentials, Cloud SQL admin access) would expose both. At Salon Lyol's scale this is acceptable; in Phase 3 multi-tenant hardening, per-tenant DB encryption keys (CMEK per tenant) or physical isolation becomes a consideration.
- RLS adds a small per-query overhead (negligible at this scale).
- The migration DB role (superuser) bypasses RLS — migration scripts must be reviewed to never select production data, only mutate schema.

---

## Related

- See `docs/go-live/checklist.md` for the step-by-step pre-launch tasks.
- Phase 3 multi-tenancy hardening (CLAUDE.md roadmap) will revisit CMEK and physical isolation when onboarding beta salons.
