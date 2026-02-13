# DebtFlow

[![CI](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml/badge.svg)](https://github.com/ricardocanela/debtflow/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/ricardocanela/debtflow/branch/main/graph/badge.svg)](https://codecov.io/gh/ricardocanela/debtflow)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://docs.djangoproject.com/en/5.1/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/typescript-5-blue.svg)](https://www.typescriptlang.org/)
[![Terraform](https://img.shields.io/badge/terraform-aws-purple.svg)](https://www.terraform.io/)
[![Kubernetes](https://img.shields.io/badge/k8s-helm-blue.svg)](https://kubernetes.io/)

> **To the Aktos team** — I built this to show what I can deliver. DebtFlow is a fully working debt collection platform with the same core workflows you manage at Aktos: SFTP ingestion, account state machines, collector worklists, payment processing, and real-time analytics. Every layer is production-grade — from the React frontend to Terraform on AWS. Clone it, run `make reset`, and see it live in under 2 minutes.

---

**DebtFlow is a full-stack debt collection management platform.** It ingests debtor portfolios via SFTP, distributes accounts to collectors, tracks every contact and payment, and delivers real-time analytics — all on a cloud-native, audit-ready infrastructure.

## Try It Now

```bash
git clone https://github.com/ricardocanela/debtflow.git && cd debtflow
make reset    # builds everything, seeds data, uploads SFTP samples (~2 min)
```

Then open **http://localhost:3000** and log in:

| Role | Username | Password |
|------|----------|----------|
| **Agency Admin** | `demo.admin` | `Demo@2026` |
| **Collector** | `sarah.mitchell` | `Collector@2026` |

The admin sees the full dashboard, analytics, imports, and settings. The collector sees only their assigned worklist.

---

## What It Does

```
SFTP Server                    DebtFlow                           Frontend
    │                             │                                  │
    │  CSV files (portfolios)     │                                  │
    ├────────────────────────────►│  Celery polls every 15 min       │
    │                             │  Pydantic validates each row     │
    │                             │  Upserts Debtor + Account        │
    │                             │                                  │
    │                             │  Admin assigns → Collectors      │
    │                             │  Collectors work accounts        │
    │                             │  Payments via Stripe             │
    │                             │                                  │
    │                             │  KPIs, trends, aging reports ───►│  Real-time dashboards
    │                             │  Audit trail for every action    │
```

### Core Workflow

| Step | What Happens | Status |
|------|-------------|--------|
| **Import** | CSV arrives via SFTP, Celery processes in batches of 1000 | `NEW` |
| **Assign** | Admin distributes accounts to collectors | `ASSIGNED` |
| **Contact** | Collector reaches debtor, logs notes | `IN_CONTACT` |
| **Negotiate** | Payment terms discussed | `NEGOTIATING` |
| **Plan** | Debtor agrees to payment plan | `PAYMENT_PLAN` |
| **Collect** | Payments recorded (Stripe or manual), balance auto-updated | `SETTLED` |
| **Close** | Debt resolved, commission calculated | `CLOSED` |

Every transition is validated by a **state machine** — no invalid jumps allowed. Every action is logged in an **immutable audit trail**.

---

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

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Ant Design, Redux Toolkit (RTK Query) |
| **Backend** | Django 5.1, Django REST Framework, drf-spectacular (OpenAPI) |
| **Auth** | JWT (SimpleJWT) — access tokens (15 min), refresh (7 days), role claims |
| **Data Pipeline** | Celery workers + Beat scheduler, Pydantic validation, batch processing |
| **Database** | PostgreSQL 16 (pg_trgm for fuzzy search, uuid-ossp, pg_stat_statements) |
| **Payments** | Stripe integration with circuit breaker, webhooks, idempotency keys |
| **Monitoring** | Prometheus + Grafana (4 dashboards, 9 alert rules), audit trail |
| **Infrastructure** | Terraform (9 AWS modules), Helm chart, GitHub Actions CI/CD |

---

## Features

### For the Agency Admin
- **Dashboard** — KPIs: active accounts, total balance, recovery rate, amount collected
- **Analytics** — Collector performance, payment trends (daily/weekly/monthly), aging report
- **SFTP Imports** — Automatic polling + manual trigger, job tracking with error details per row
- **Settings** — Agency config, collector management (commission rates, account limits)

### For the Collector
- **Worklist** — Personal queue filtered by status, priority, and balance range
- **Account Detail** — Full timeline (notes, payments, status changes, imports), debtor info
- **Actions** — Add notes, transition status (validated), record payments

### Data Pipeline
- **SFTP Polling** — Celery Beat polls every 15 min, or trigger manually from the UI
- **Validation** — Each CSV row validated with Pydantic before database insertion
- **Batch Processing** — 1000 records per transaction, errors isolated per row
- **Idempotency** — `update_or_create` by `external_ref` — re-imports update, never duplicate
- **Retry Logic** — 3 retries (polling) / 2 retries (processing) with exponential backoff
- **Job Tracking** — Status, counts (ok/errors), error details with line numbers

### Payments
- **Stripe Integration** — Credit card, bank transfer, check, cash
- **Circuit Breaker** — Protects against Stripe outages (5 failures → open → 30s recovery)
- **Webhooks** — Async confirmation via Stripe webhook with signature verification
- **Idempotency** — Prevents duplicate payments via idempotency key

### Security & Compliance
- **JWT Authentication** with short-lived tokens and role-based access control
- **Immutable Audit Trail** — who, what, when, IP address, field-level diffs
- **Encrypted SSN** at rest (last 4 digits only)
- **Network Policies** — Pod-level isolation in Kubernetes
- **IRSA** — Per-pod AWS permissions (principle of least privilege)

---

## Data Ingestion — Deep Dive

```
┌─────────────┐     poll      ┌──────────┐    download    ┌──────────┐
│ SFTP Server │ ◄──────────── │  Celery  │ ──────────────►│  /tmp/   │
│ (per agency)│               │  Beat    │                │  CSV     │
└─────────────┘               └──────────┘                └────┬─────┘
                                                               │
                              ┌──────────┐    validate    ┌────▼─────┐
                              │ Pydantic │ ◄───────────── │ CSVParser│
                              │ Schema   │                │          │
                              └────┬─────┘                └──────────┘
                                   │
                              ┌────▼──────────────┐
                              │  BatchImporter     │
                              │  1000 rows/batch   │
                              │  atomic per row    │
                              │  upsert Debtor     │
                              │  upsert Account    │
                              │  create Activity   │
                              └────┬──────────────┘
                                   │
                              ┌────▼─────┐
                              │ Import   │
                              │ Job      │  status, ok, errors,
                              │ (DB)     │  error_details[]
                              └──────────┘
```

### CSV Format

| Column | Required | Validation |
|--------|----------|------------|
| `external_ref` | Yes | Unique identifier, used for upsert |
| `debtor_name` | Yes | Non-empty string |
| `original_amount` | Yes | Positive decimal |
| `debtor_ssn_last4` | No | Exactly 4 digits |
| `debtor_email` | No | Valid email format |
| `debtor_phone` | No | Phone string |
| `due_date` | No | YYYY-MM-DD |
| `creditor_name` | No | String |
| `account_type` | No | String |

### Testing the Pipeline

```bash
make sftp-upload    # Upload 3 sample CSVs (30 records total)
                    # Then click "Trigger Import" on /imports
make sftp-status    # See pending vs. processed files
make sftp-reload    # Clear and re-upload for another cycle
```

---

## API

Interactive docs at **http://localhost:8000/api/v1/docs/** (Swagger UI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/token/` | Login (JWT access + refresh) |
| `POST` | `/api/v1/auth/token/refresh/` | Renew access token |
| `GET` | `/api/v1/auth/me/` | Current user profile + role |
| `GET` | `/api/v1/accounts/` | List accounts (filtered, paginated, searchable) |
| `GET` | `/api/v1/accounts/{id}/` | Account detail with debtor info |
| `POST` | `/api/v1/accounts/{id}/transition/` | Status transition (validated) |
| `POST` | `/api/v1/accounts/{id}/assign/` | Assign to collector |
| `POST` | `/api/v1/accounts/{id}/add_note/` | Add note to timeline |
| `GET/POST` | `/api/v1/payments/` | List / record payments |
| `POST` | `/api/v1/payments/{id}/refund/` | Refund a payment |
| `POST` | `/api/v1/payments/webhook/stripe/` | Stripe webhook receiver |
| `GET` | `/api/v1/imports/` | List import jobs with counts |
| `POST` | `/api/v1/imports/trigger/` | Manually trigger SFTP poll |
| `GET` | `/api/v1/analytics/dashboard/` | KPIs (accounts, balance, recovery rate) |
| `GET` | `/api/v1/analytics/collectors/` | Per-collector performance |
| `GET` | `/api/v1/analytics/payments/trends/` | Payment time series |
| `GET` | `/api/v1/analytics/aging-report/` | Account aging distribution |

---

## Infrastructure

### AWS (Terraform — 9 modules)

```
┌────────────────────────────────────────────────────────┐
│                      AWS Account                       │
│                                                        │
│  ┌──────────────── VPC (10.0.0.0/16) ───────────────┐ │
│  │  Public Subnets        Private Subnets            │ │
│  │  ├── NAT Gateway       ├── EKS Worker Nodes       │ │
│  │  └── ALB               ├── RDS PostgreSQL 16      │ │
│  │                        └── ElastiCache Redis 7    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                        │
│  ECR (API + Frontend)    Secrets Manager    Route53    │
│  S3 (file storage)       IAM/IRSA           ACM/SSL   │
└────────────────────────────────────────────────────────┘
```

| Module | What It Manages |
|--------|----------------|
| `networking` | VPC, public/private subnets, NAT Gateway, Internet Gateway |
| `eks` | EKS cluster, node groups, managed addons (CoreDNS, VPC CNI, EBS CSI) |
| `database` | RDS PostgreSQL 16 (Multi-AZ in production) |
| `cache` | ElastiCache Redis 7 |
| `storage` | S3 with lifecycle (90d → Glacier, 365d → delete) |
| `ecr` | Container registries for API and Frontend images |
| `iam` | IRSA roles — worker (S3), API (Secrets), ALB controller |
| `secrets` | Secrets Manager — DB password, Django key, Stripe, SFTP |
| `dns` | Route53 hosted zone + ACM wildcard certificate |

### Kubernetes (Helm Chart)

- **API** — Gunicorn, 3 replicas (prod), service account with IRSA
- **Worker** — Celery, 2 replicas, S3 + SFTP access
- **Beat** — Celery scheduler, 1 replica
- **Frontend** — Nginx serving React SPA, 2 replicas
- **Ingress** — ALB, `/api/*` → API, `/*` → Frontend
- **HPA** — Auto-scaling 3-10 pods at 70% CPU
- **PDB** — Min 2 pods available during maintenance
- **Network Policies** — Per-component traffic isolation
- **Migration Job** — Helm hook runs `manage.py migrate` before each deploy
- **CronJobs** — Weekly VACUUM, monthly audit log archival

### CI/CD (GitHub Actions)

```
Push to main ──► CI Tests ──► Build API + Frontend ──► Push ECR ──► Deploy Staging
                                                                        │
Tag v*.*.* ──► Build ──► Push ECR ──► Deploy Production ──► Health Check
                                                               ├── OK → Done
                                                               └── Fail → Auto Rollback
```

### Environments

| Environment | URL | Trigger |
|-------------|-----|---------|
| **Local** | localhost:3000 / :8000 | `make reset` |
| **Staging** | staging.debtflow.example.com | Push to `main` |
| **Production** | debtflow.example.com | Tag `v*.*.*` |

---

## Observability

| Tool | URL | What It Shows |
|------|-----|---------------|
| **Grafana** | localhost:3001 | 4 dashboards (API, DB, Business, Celery) |
| **Prometheus** | localhost:9090 | Metrics scraping (15s interval) |
| **API Metrics** | localhost:8000/metrics | Django Prometheus endpoint |
| **Health Check** | localhost:8000/health/ | Container/K8s probe |
| **Swagger** | localhost:8000/api/v1/docs/ | Interactive API docs |

**Grafana Dashboards:** API Overview (RPS, error rate, P95 latency) · Database Health (connections, query duration, cache hit ratio) · Business Metrics (payments/hour, collected today, import success rate) · Celery Workers (tasks/min, duration by type, failures)

**9 Alert Rules:** High API latency · High error rate · Database connections · Celery queue backlog · SFTP import failures · Stripe circuit breaker · Pod crash loops · Disk usage

---

## Development

### Makefile Commands

```bash
make help           # Show all commands
make reset          # Full reset: rebuild, seed, upload SFTP (~2 min)
make dev-d          # Start services in background
make down           # Stop services
make seed           # Seed demo data (85 accounts, 163 payments, etc.)
make seed-clear     # Clear and re-seed
make sftp-upload    # Upload sample CSVs to SFTP server
make sftp-reload    # Clear SFTP + re-upload (ready for new import cycle)
make sftp-status    # Show pending vs. processed files
make worker-logs    # Tail Celery worker logs
make api-logs       # Tail API logs
make shell          # Django shell
make test           # Tests with coverage
make lint           # Ruff lint + format
make helm-lint      # Lint Helm chart
make tf-validate    # Validate Terraform
```

### Seed Data

`make seed` creates a realistic demo environment:

- **1 Agency** — Apex Recovery Solutions (SFTP enabled)
- **4 Collectors** — With commission rates and account limits
- **85 Accounts** — Across all 8 statuses with weighted distribution
- **163 Payments** — Completed, pending, and failed
- **442 Activities** — Full timeline history
- **7 Import Jobs** — With real success/error counts

---

## Documentation

| Document | Description |
|----------|-------------|
| [Product Overview](docs/debtflow-product.md) | Full product description, value proposition, features |
| [Infrastructure Guide](docs/aula-infraestrutura-aws-kubernetes.md) | Complete AWS + Kubernetes walkthrough |
| [Architecture](docs/architecture.md) | System design and component overview |
| [ADRs](docs/adrs/) | Architecture Decision Records |
| [Runbooks](docs/runbooks/) | Incident response procedures |
| [API Guide](docs/api.md) | Detailed API documentation |

---

**Author:** Ricardo Lima Canela — [github.com/ricardocanela](https://github.com/ricardocanela)
