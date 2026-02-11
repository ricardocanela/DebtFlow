# DebtFlow

[![CI](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml/badge.svg)](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/ricardocanela/debtflow/branch/main/graph/badge.svg)](https://codecov.io/gh/ricardocanela/debtflow)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://docs.djangoproject.com/en/5.1/)

> **Hey Aktos recruiters!** If you're checking this out, I'd love to work with you! 😄 Feel free to get inspired by this code and let me know if you want me to make this repo private.  
> I am working on something beautiful for Aktos. Wait for it.

**Debt Collection Management Platform** — A backend system for debt collection agencies to manage delinquent accounts, process payments, and ingest data via SFTP.

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
