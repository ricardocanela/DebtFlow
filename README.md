# DebtFlow

[![CI](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml/badge.svg)](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/ricardocanela/debtflow/branch/main/graph/badge.svg)](https://codecov.io/gh/ricardocanela/debtflow)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://docs.djangoproject.com/en/5.1/)

> **Hey Aktos recruiters!** If you're checking this out, I'd love to work with you! 😄 Feel free to get inspired by this code and let me know if you want me to make this repo private.  
> I am working on something beautiful for Aktos. Wait for it.

**Debt Collection Management Platform** — A production-ready backend system for debt collection agencies to manage delinquent accounts, process payments, and ingest portfolio data via SFTP.

## Architecture

```
                    Internet
                       │
              ┌────────▼────────┐
              │    AWS ALB      │
              │    + nginx      │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │                           │
  ┌──────▼──────┐           ┌───────▼───────┐
  │ Django API   │           │ Django API    │
  │ (Gunicorn)   │           │ (Gunicorn)    │
  └──────┬──────┘           └───────┬───────┘
         │                           │
    ┌────▼───┬────┬─────────┬───────▼──┐
    │        │    │         │          │
  ┌─▼──┐  ┌─▼─┐  ┌─▼─┐  ┌──▼─┐  ┌───▼───┐
  │PgSQL│  │Red│  │ S3│  │SQS │  │Celery │
  │ RDS │  │is │  │   │  │DLQ │  │Workers│
  └─────┘  └───┘  └───┘  └────┘  └───────┘
```

**Stack:** Django 5.1, DRF, PostgreSQL 16, Celery 5, Redis 7, Docker, Kubernetes, Helm, Terraform, GitHub Actions, Prometheus, Grafana

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/ricardocanela/debtflow.git
cd debtflow

# Start all services
make dev
```

This starts: API server, Celery worker, Celery Beat, PostgreSQL, Redis, SFTP test server, Prometheus, and Grafana.

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
make migrate

# Seed data
make seed

# Start server
python manage.py runserver
```

## API Documentation

Once running, access the interactive API docs at:

- **Swagger UI:** http://localhost:8000/api/v1/docs/
- **OpenAPI Schema:** http://localhost:8000/api/v1/schema/

### Key Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/v1/auth/token/` | Obtain JWT token |
| `GET /api/v1/accounts/` | List accounts (filtered, paginated) |
| `POST /api/v1/accounts/{id}/assign/` | Assign to collector |
| `POST /api/v1/accounts/{id}/transition/` | Status transition |
| `POST /api/v1/payments/` | Record payment |
| `POST /api/v1/payments/webhook/stripe/` | Stripe webhook |
| `GET /api/v1/imports/` | List SFTP import jobs |
| `GET /api/v1/analytics/dashboard/` | Dashboard KPIs |

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

## Testing

```bash
make test          # All tests with coverage
make test-unit     # Unit tests only
make test-integration  # Integration tests only
make lint          # Ruff lint + format check
make typecheck     # Mypy type checking
```

## Infrastructure

- **Terraform:** `infra/terraform/` — AWS modules (VPC, EKS, RDS, ElastiCache, S3)
- **Helm:** `infra/helm/debtflow/` — Kubernetes deployment chart
- **CI/CD:** `.github/workflows/` — GitHub Actions pipelines
- **Monitoring:** `monitoring/` — Prometheus + Grafana dashboards

## Documentation

- [Architecture Overview](docs/architecture.md)
- [ADRs](docs/adrs/) — 8 Architecture Decision Records
- [Runbooks](docs/runbooks/) — Incident response procedures
- [API Guide](docs/api.md)

## License

This is a portfolio project. Not licensed for production use.

---

**Author:** Ricardo Lima Canela — [github.com/ricardocanela](https://github.com/ricardocanela)
