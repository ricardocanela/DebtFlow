# DebtFlow

[![CI](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml/badge.svg)](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/ricardocanela/debtflow/branch/main/graph/badge.svg)](https://codecov.io/gh/ricardocanela/debtflow)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://docs.djangoproject.com/en/5.1/)

> **Hey Aktos recruiters!** If you're checking this out, I'd love to work with you! 😄 Feel free to get inspired by this code and let me know if you want me to make this repo private.  
> I am working on something beautiful for Aktos. Wait for it.

**Debt Collection Management Platform** — A full-stack, production-ready system for collection agencies to manage delinquent accounts, process payments, and ingest portfolio data via SFTP.

## Architecture

```
                    ┌─────────────────────┐
                    │   Browser / Client  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    ALB / Ingress    │
                    └───┬────────────┬────┘
                        │            │
                   /api/*          /*
                        │            │
                 ┌──────▼──────┐  ┌──▼───────────┐
                 │   API Pods  │  │ Frontend Pods │
                 │  Gunicorn   │  │    Nginx      │
                 │  :8000      │  │    :80        │
                 └──────┬──────┘  └───────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐
     │  Worker  │ │   Beat   │ │ Migrate  │
     │  Celery  │ │ Scheduler│ │   Job    │
     └────┬─────┘ └────┬─────┘ └──────────┘
          │             │
     ┌────┴─────────────┴────┐
     │                       │
     ▼                       ▼
┌──────────┐          ┌──────────┐      ┌─────┐
│ Postgres │          │  Redis   │      │  S3 │
│   16     │          │    7     │      │     │
└──────────┘          └──────────┘      └─────┘
```

### Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + TypeScript + Ant Design + Redux Toolkit (RTK Query) |
| **Backend API** | Django 5.1 + Django REST Framework + drf-spectacular (OpenAPI) |
| **Authentication** | JWT (SimpleJWT) with refresh token and custom role claims |
| **Async Tasks** | Celery + Redis (broker) |
| **Scheduler** | Celery Beat |
| **Database** | PostgreSQL 16 (uuid-ossp, pg_trgm, pg_stat_statements) |
| **Cache** | Redis 7 |
| **Storage** | AWS S3 |
| **Monitoring** | Prometheus + Grafana |
| **Infrastructure** | AWS EKS (Kubernetes) + Terraform + Helm |
| **CI/CD** | GitHub Actions (OIDC, dual image build, health check + rollback) |

## Quick Start

### Prerequisites

- Docker & Docker Compose

### Run with Docker

```bash
# 1. Clone the repository
git clone https://github.com/ricardocanela/debtflow.git
cd debtflow

# 2. Start the full environment
cd docker && docker compose up -d

# 3. Seed demo data (creates agencies, collectors, accounts, payments, imports)
docker compose exec api python manage.py seed_demo

# 4. Access the application
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/api/v1/docs/
# Grafana:   http://localhost:3001 (admin/admin)
```

This starts: **Frontend** (React dev server), **API** (Django + Gunicorn), **Celery worker**, **Celery Beat**, **PostgreSQL**, **Redis**, **SFTP test server**, **Prometheus**, and **Grafana**.

### Demo Credentials

The `seed_demo` command creates realistic demo data with the following user accounts:

| Role | Username | Password | Access |
|------|----------|----------|--------|
| **Agency Admin** | `demo.admin` | `Demo@2026` | Full dashboard, all accounts, imports, settings, analytics |
| **Collector** | `sarah.mitchell` | `Collector@2026` | Personal worklist, assigned accounts only |
| **Collector** | `james.carter` | `Collector@2026` | Personal worklist, assigned accounts only |
| **Collector** | `maria.gonzalez` | `Collector@2026` | Personal worklist, assigned accounts only |
| **Collector** | `david.thompson` | `Collector@2026` | Personal worklist, assigned accounts only |

### Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Superuser** | Platform administrator | Full access to everything including Django Admin |
| **Agency Admin** | Agency manager/owner | Dashboard, all accounts in their agency, imports, settings, collector management |
| **Collector** | Debt collector | Personal worklist, assigned accounts, add notes, record payments, change status |

### Seed Data Details

The `seed_demo` command populates the database with:

- **1 Agency** — Apex Recovery Solutions (SFTP enabled)
- **85 Debtors** — Realistic US names, addresses, emails, phones
- **85 Accounts** — Across all statuses (NEW, ASSIGNED, IN_CONTACT, NEGOTIATING, PAYMENT_PLAN, SETTLED, CLOSED, DISPUTED)
- **163 Payments** — Completed, pending, and failed payments
- **442 Activities** — Import records, assignments, status changes, notes, payments
- **7 Import Jobs** — 6 completed, 1 in progress
- **4 Collectors** — Assigned to the agency with commission rates
- **1 Payment Processor** — Stripe (test mode)

```bash
# Reset and re-seed demo data
docker compose exec api python manage.py seed_demo --clear
```

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements/local.txt

# Copy environment file
cp .env.example .env

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_demo

# Start server
python manage.py runserver
```

## Frontend

The frontend is a **React 18 SPA** built with TypeScript, Ant Design, and Redux Toolkit (RTK Query).

### Key Pages

| Page | Route | Description |
|------|-------|-------------|
| **Login** | `/login` | JWT authentication with role-based redirect |
| **Dashboard** | `/dashboard` | KPIs, recovery rate, payment trends, aging report |
| **Worklist** | `/worklist` | Collector's assigned accounts with filters and search |
| **Account Detail** | `/accounts/:id` | Full account view with timeline, debtor info, payments |
| **Imports** | `/imports` | SFTP import job history with trigger button |
| **Settings** | `/settings` | Agency and collector management |

### Frontend Architecture

```
frontend/
├── src/
│   ├── api/            # RTK Query API slices (accounts, payments, imports, analytics)
│   ├── components/     # Reusable UI components organized by feature
│   ├── pages/          # Page-level components (Dashboard, Worklist, etc.)
│   ├── hooks/          # Custom hooks (useRole, useAuth)
│   ├── store/          # Redux store configuration
│   └── types/          # TypeScript type definitions
```

## API Documentation

Once running, access the interactive API docs at:

- **Swagger UI:** http://localhost:8000/api/v1/docs/
- **OpenAPI Schema:** http://localhost:8000/api/v1/schema/

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/token/` | Login (returns access + refresh JWT) |
| POST | `/api/v1/auth/token/refresh/` | Renew access token |
| GET | `/api/v1/auth/me/` | Authenticated user profile |
| GET | `/api/v1/accounts/` | List accounts (filtered, paginated) |
| GET | `/api/v1/accounts/{id}/` | Account detail |
| POST | `/api/v1/accounts/{id}/transition/` | Change account status |
| POST | `/api/v1/accounts/{id}/assign/` | Assign to collector |
| POST | `/api/v1/accounts/{id}/add_note/` | Add note to timeline |
| GET | `/api/v1/payments/` | List payments |
| POST | `/api/v1/payments/` | Record payment |
| POST | `/api/v1/payments/{id}/refund/` | Refund payment |
| POST | `/api/v1/payments/webhook/stripe/` | Stripe webhook |
| GET | `/api/v1/imports/` | List import jobs |
| POST | `/api/v1/imports/trigger/` | Manually trigger SFTP import |
| GET | `/api/v1/analytics/dashboard/` | Dashboard KPIs |
| GET | `/api/v1/analytics/collectors/` | Collector performance |
| GET | `/api/v1/analytics/payments/trends/` | Payment trends |
| GET | `/api/v1/analytics/aging-report/` | Aging report |

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo.admin", "password": "Demo@2026"}'

# Response: {"access": "eyJ...", "refresh": "eyJ..."}

# Use the token
curl http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer eyJ..."
```

## Data Ingestion

The platform automatically ingests debt portfolio files from creditor clients via **SFTP polling**.

### How It Works

1. **Scheduled Polling**: Celery Beat runs `sftp_poll_all_agencies` every 15 minutes
2. **File Discovery**: For each active agency with SFTP enabled, the system:
   - Connects to the configured SFTP server
   - Lists CSV files in the remote directory
   - Downloads new files to temporary storage
3. **Async Processing**: Each file triggers a Celery task (`process_import_file`) that:
   - Parses the CSV with Pydantic validation
   - Processes records in batches of 1000
   - Upserts `Debtor` records by `external_ref`
   - Creates/updates `Account` records by `external_ref`
   - Isolates errors per row (one bad record doesn't block the batch)
4. **Job Tracking**: Each import creates an `SFTPImportJob` record with:
   - Status (processing, completed, failed)
   - Counts (total, processed_ok, processed_errors)
   - Error details with line numbers and validation messages

### Reliability Features

- **Idempotency**: Imports are idempotent via `update_or_create` on `external_ref`. Re-importing the same file updates existing records instead of creating duplicates.
- **Retry Logic**: 
  - Polling task (`sftp_poll_all_agencies`): 3 retries with 60s delay on transient failures
  - Import task (`process_import_file`): 2 retries with 120s delay on processing errors
  - Failed imports are tracked in `SFTPImportJob` with detailed error logs for debugging

### CSV Format

Required columns:
- `external_ref` (unique identifier)
- `debtor_name`
- `original_amount` (must be positive)

Optional columns:
- `debtor_ssn_last4` (exactly 4 digits)
- `debtor_email`
- `debtor_phone`
- `due_date` (YYYY-MM-DD format)
- `creditor_name`
- `account_type`

### Testing SFTP Ingestion

```bash
# Upload test CSV files to the SFTP test server
python scripts/sftp_test_upload.py

# Check import jobs via API
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/imports/
```

## Local URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React SPA (Vite dev server) |
| **API** | http://localhost:8000 | Django REST API |
| **Swagger UI** | http://localhost:8000/api/v1/docs/ | Interactive API documentation |
| **Django Admin** | http://localhost:8000/admin/ | Django admin panel |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **Grafana** | http://localhost:3001 | Dashboards (admin/admin) |
| **API Metrics** | http://localhost:8000/metrics | Prometheus endpoint |
| **Health Check** | http://localhost:8000/health/ | API health verification |

## Testing

```bash
make test          # All tests with coverage
make test-unit     # Unit tests only
make test-integration  # Integration tests only
make lint          # Ruff lint + format check
make typecheck     # Mypy type checking
```

## Infrastructure

- **Terraform:** `infra/terraform/` — AWS modules (VPC, EKS, RDS, ElastiCache, S3, ECR, IAM, Secrets, DNS)
- **Helm:** `infra/helm/debtflow/` — Kubernetes deployment chart (API, Worker, Beat, Frontend)
- **CI/CD:** `.github/workflows/` — GitHub Actions pipelines (dual image build, health check + rollback)
- **Monitoring:** `monitoring/` — Prometheus + Grafana dashboards

## Documentation

- [Product Overview](docs/debtflow-product.md) — Full product description, features, and value proposition
- [AWS & Kubernetes Infrastructure](docs/aula-infraestrutura-aws-kubernetes.md) — Complete infrastructure guide
- [Architecture Overview](docs/architecture.md)
- [ADRs](docs/adrs/) — Architecture Decision Records
- [Runbooks](docs/runbooks/) — Incident response procedures
- [API Guide](docs/api.md)

## License

This is a portfolio project. Not licensed for production use.

---

**Author:** Ricardo Lima Canela — [github.com/ricardocanela](https://github.com/ricardocanela)
