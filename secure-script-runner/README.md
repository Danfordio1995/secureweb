# Secure Script Runner (MVP)

A secure, production-grade system to register server-side scripts, templatize them into **Modules**, assign to users/groups, and execute each run in an isolated sandbox with strong validation, RBAC, and audit logging.

> **MVP status**: This repository provides a working backend API, job executor with container-per-execution (via Docker), Redis queue, PostgreSQL schema, MinIO artifact storage, seed data, and a minimal Next.js UI for demo. It covers the acceptance criteria with a simplified approval flow and redaction.

---

## Quick start (Docker Compose)

### Prereqs
- Docker 24+
- Docker Compose v2

```bash
cp .env.example .env
# Edit values as needed
docker compose up -d --build
# Seed data (scripts, module v1, user assignment)
docker compose exec api python -m app.seed
```

Open:
- API docs (OpenAPI): http://localhost:8080/docs
- UI: http://localhost:3000

Login header: For demo, use `X-Demo-User: analyst@example.com` to impersonate a user, or `X-Demo-User: admin@example.com` for admin. In production, enable OIDC (see **Auth** below).

---

## Services
- **api**: FastAPI app with RBAC, parameter validation, audit logs, SIEM webhook, S3/MinIO artifact storage, OpenAPI.
- **worker**: Celery worker that provisions a **container per execution** using the `runner` image and Docker Engine API, mounts scripts read-only and creates a temporary `/work` dir.
- **redis**: Queue/broker for Celery and short-lived state.
- **postgres**: Primary database storing users, groups, scripts, modules, executions, logs, artifacts, audit logs.
- **minio**: S3-compatible object storage for artifacts; presigned URLs provided by API.
- **ui**: Next.js minimal UI for Admin/User dashboards.

---

## Security Highlights (MVP)
- **Container-per-execution** (`--network none`, non-root, read-only script mount).
- **No shell concatenation**: all commands built as **argv arrays**.
- **Interpreter & script-path allowlists** under `/opt/scripts`.
- **Strict parameter schema** (type, enum/range/regex). Unknown inputs rejected.
- **Secrets** are masked in UI/logs; injected via env vars or temp files, then shredded.
- **Resource limits**: timeout, memory, CPU (via Docker constraints), max output size.
- **Egress deny**: execution containers run with no network by default.
- **SSO-ready**: OIDC/Entra ID JWT validation supported; demo uses header-based auth.
- **Audit logs** with before/after, IP, UA; optional SIEM webhook.

> Review `app/services/command_builder.py`, `app/worker/executor.py`, and `runner/Dockerfile` for the critical security pieces.

---

## Auth
- **Production**: Configure OIDC (Azure Entra ID) by setting `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL` in `.env`, and set `AUTH_MODE=oidc`.
- **Demo**: Set `AUTH_MODE=demo_header` (default). The API trusts header `X-Demo-User` to impersonate a user. **Do not use in production**.

---

## Script base directory
Scripts must live under the allowlisted base directory inside the runner container: `/opt/scripts`. In Compose we bind `./scripts` to `/opt/scripts:ro`.

Sample script provided: `scripts/backup_db.py`.

---

## Acceptance Criteria (Mapping)
1. **Register** `/opt/scripts/backup_db.py` (python3) → Seed does this, creating Module v1 with params: `db_name (enum)`, `retention_days (int)`, `notify_email (string)`, `backup_key (secret)`.
2. **Assign** to `analyst@example.com` with `run+view` → Seed.
3. **Run** module, live logs visible, artifact `backup.log` downloadable, secrets never appear → Demo UI & API.
4. **Timeout** enforced → configure `timeout_sec` in module; worker terminates container and marks `timeout`.
5. **Approval workflow** (1 approver) → Toggle on the module; run blocks until approved by an Admin; audit trail captured.
6. **SIEM** receives audit events → set `SIEM_WEBHOOK_URL` in `.env` (optional); API posts JSON events.
7. **Injection & traversal** attempts blocked by validation and allowlists.

---

## Dev scripts
```bash
# API lint
docker compose exec api ruff check app
# Tests (subset)
docker compose exec api pytest -q
```

---

## License
MIT (for demo). Review and harden before production.
