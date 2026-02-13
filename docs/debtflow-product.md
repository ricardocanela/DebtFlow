# DebtFlow — Product Overview

## What is DebtFlow?

DebtFlow is a comprehensive debt collection management platform designed for collection agencies that need to manage large volumes of delinquent accounts with efficiency, regulatory compliance, and full transparency.

The platform replaces spreadsheets, legacy systems, and manual processes with a unified digital workflow — from debtor data import to payment receipt, with complete traceability of every action.

---

## Elevator Pitch

> *"DebtFlow is the operating system for modern collection agencies. It automatically imports accounts via SFTP, distributes them to collectors, tracks every contact and payment, and delivers real-time analytics — all on a secure, scalable, audit-ready cloud-native platform."*

**In one sentence:** We turn the chaos of debt collection into a predictable and measurable workflow.

---

## The Problem We Solve

| Market Pain Point | How DebtFlow Solves It |
|---------------|------------------------|
| Debtor data arrives via SFTP in different formats | Automated import with validation, mapping, and error logging |
| Collectors use spreadsheets and there is no pipeline visibility | Individual worklist with filters, priorities, and real-time status |
| Managers do not know who is performing | Dashboard with KPIs per collector, recovery rate, and trends |
| Payments are tracked manually | Stripe integration for card, bank slip, and wire transfer payments |
| Audits require complete history | Immutable audit trail logging every action, IP, and timestamp |
| Legacy systems do not scale | Cloud-native architecture on AWS with Kubernetes, auto-scaling, and HA |

---

## Value Proposition

### For the Agency Owner
- **Full visibility** of the portfolio in a single dashboard
- **Increased recovery rate** through intelligent prioritization and balanced distribution
- **Reduced regulatory risk** with a complete audit trail and FDCPA/TCPA compliance

### For the Operations Manager
- **Performance metrics** per collector in real time
- **Automated import** of new accounts with no manual intervention
- **Aging reports** to identify stagnant accounts

### For the Collector
- **Personal worklist** with all assigned accounts sorted by priority
- **Complete history** for each account (notes, payments, status changes)
- **Guided workflow** — each account has a clear state and available actions

---

## Core Features

### 1. Account Management

The core of the system. Each account represents a delinquent debt linked to a debtor.

**State Machine:**
```
NEW → ASSIGNED → IN_CONTACT → NEGOTIATING → PAYMENT_PLAN → SETTLED → CLOSED
                                    ↓               ↓
                                DISPUTED ←──────────┘
```

- Each transition is validated (invalid jumps are not allowed)
- Each status change generates a record in the account timeline
- Priorities from 0-3 for worklist ordering

**Debtor Data:**
- Full name with fuzzy search (trigram)
- Phone, email, full address
- Partial SSN (last 4 digits, encrypted at rest)
- External reference for traceability with the source system

### 2. Collector Worklist

The collector's main day-to-day screen:

- Filters by status, priority, value range
- Search by debtor name or external reference
- Sorting by creation date, balance, or priority
- Quick access to account detail with a single click
- Visual indicators for high-priority accounts

### 3. Account Detail

Full-page view with all information for an account:

- **Summary**: current vs. original balance, status, priority, due date
- **Debtor Data**: full contact information, address, reference
- **Assigned Collector**: name, commission rate
- **Activity Timeline**: all actions in chronological order
  - Manual notes from the collector
  - Status changes
  - Payments received
  - Assignments
  - Imports
- **Available Actions**:
  - Add note
  - Change status (only valid transitions)
  - Record payment

### 4. Payments

Complete payment lifecycle management:

- **Methods**: Credit card, bank transfer, check, cash
- **Status**: Pending → Completed / Failed / Refunded
- **Stripe Integration**: automatic processing with webhook for confirmation
- **Idempotency key**: prevents duplicate payments
- **Metadata**: additional processor data (last 4 digits, transaction ID)

### 5. Data Import (SFTP)

Automated data ingestion workflow:

1. **Automatic polling**: Celery Beat schedules periodic checks of the SFTP server
2. **Download**: CSV file is downloaded and stored in S3
3. **Processing**: each row is validated and inserted as Debtor + Account
4. **Report**: total records, successes, errors with per-row details
5. **History**: all import jobs are visible in the interface

**Real-time monitoring**: jobs in progress display their progress (32/45 records processed).

### 6. Dashboard and Analytics

Metrics calculated in real time from operational data:

- **Dashboard KPIs**:
  - Total active accounts
  - Total balance to recover
  - Recovery rate (%)
  - Total collected in the period

- **Collector Performance**:
  - Accounts assigned per collector
  - Amount recovered per collector
  - Individual conversion rate

- **Payment Trends**:
  - Time-series chart (daily/weekly/monthly)
  - Payment volume and value over time

- **Aging Report**:
  - Distribution of accounts by age range (0-30, 31-60, 61-90, 90+ days)
  - Visual identification of stagnant accounts

### 7. Settings and Administration

- **Agency Management**: name, license, customizable settings
- **Collector Management**: registration, activation/deactivation, commission rate, account limit
- **Django Admin**: full panel for advanced operations
- **Access Control**: roles (superuser, agency_admin, collector) with per-page guards

### 8. Audit Trail

Immutable record of all actions in the system:

- Who did it, what was done, when it was done
- Change diff (old vs. new values)
- Source IP
- Prepared for monthly partitioning and 24-month retention

---

## Technical Architecture

### Stack

| Layer | Technology |
|--------|-----------|
| **Frontend** | React 18 + TypeScript + Ant Design + Redux Toolkit (RTK Query) |
| **Backend API** | Django 5.1 + Django REST Framework + drf-spectacular (OpenAPI) |
| **Authentication** | JWT (SimpleJWT) with refresh token and custom claims |
| **Async Tasks** | Celery + Redis (broker) |
| **Scheduler** | Celery Beat |
| **Database** | PostgreSQL 16 with extensions (uuid-ossp, pg_trgm, pg_stat_statements) |
| **Cache** | Redis 7 |
| **Storage** | AWS S3 |
| **Monitoring** | Prometheus + Grafana |
| **Infrastructure** | AWS EKS (Kubernetes) + Terraform + Helm |
| **CI/CD** | GitHub Actions (OIDC auth, dual image build, health check + rollback) |

### Component Diagram

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

### Security

- **JWT Authentication** with short-lived tokens (15 min access, 7 days refresh)
- **CORS** configured per environment
- **Network Policies** in Kubernetes (per-component isolation)
- **IRSA** (IAM Roles for Service Accounts) — each pod has minimal AWS permissions
- **Secrets Manager** — passwords and keys never in code
- **Encrypted SSN** at rest
- **Immutable audit trail** for compliance

---

## How to Use

### Getting Started (Local Development)

```bash
# 1. Clone the repository
git clone <repo-url> && cd debtflow

# 2. Full setup in one command (build, seed, upload SFTP samples)
make reset

# 3. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/v1/docs/
# Grafana:  http://localhost:3001 (admin/admin)
```

Or step by step:

```bash
make dev-d          # Start all services
make seed           # Seed demo data
make sftp-upload    # Upload sample CSVs to the SFTP test server
```

### Demo Credentials

| Role | Username | Password | Access |
|--------|----------|----------|--------|
| **Agency Admin** | demo.admin | Demo@2026 | Dashboard, all accounts, imports, settings, analytics |
| **Collector** | sarah.mitchell | Collector@2026 | Personal worklist, assigned accounts |
| **Collector** | james.carter | Collector@2026 | Personal worklist, assigned accounts |
| **Collector** | maria.gonzalez | Collector@2026 | Personal worklist, assigned accounts |
| **Collector** | david.thompson | Collector@2026 | Personal worklist, assigned accounts |

### SFTP Test Server

A local SFTP server (`atmoz/sftp`) runs as part of Docker Compose. It starts empty — sample CSVs are uploaded via `make sftp-upload`.

| Command | Description |
|---------|-------------|
| `make sftp-upload` | Upload 3 sample CSVs to the SFTP server |
| `make sftp-status` | Show pending vs. processed files |
| `make sftp-reload` | Clear and re-upload samples for a new test cycle |
| `make sftp-clear` | Remove all files from the SFTP server |

After uploading, click **"Trigger Import"** on `/imports` or wait for Celery Beat's 15-minute automatic poll. Processed files are moved to `/upload/processed/` to prevent re-importing.

### Makefile Reference

Run `make help` to see all commands. Key ones:

| Command | Description |
|---------|-------------|
| `make reset` | Full reset: destroy volumes, rebuild, seed, upload SFTP |
| `make dev-d` | Start all services in background |
| `make down` | Stop all services |
| `make seed` | Seed demo data |
| `make seed-clear` | Clear and re-seed demo data |
| `make shell` | Open Django shell |
| `make worker-logs` | Tail Celery worker logs |
| `make test` | Run all tests with coverage |
| `make lint` | Ruff lint + format check |
| `make helm-lint` | Lint Helm chart |
| `make tf-validate` | Validate Terraform |

### Typical Usage Flow

```
1. IMPORT       →  Data arrives via SFTP → Import job processes CSV
                    New accounts appear with status NEW

2. DISTRIBUTE   →  Admin assigns accounts to collectors
                    Status changes to ASSIGNED

3. CONTACT      →  Collector calls/sends email → records note
                    Status changes to IN_CONTACT

4. NEGOTIATE    →  Collector presents payment options
                    Status changes to NEGOTIATING

5. PLAN         →  Debtor accepts payment plan
                    Status changes to PAYMENT_PLAN

6. COLLECT      →  Payments are recorded (Stripe or manual)
                    Account balance is updated automatically

7. CLOSE        →  Debt paid off → Status SETTLED → CLOSED
                    Collector commission calculated automatically
```

---

## REST API

The API follows the RESTful standard with JWT authentication. Interactive documentation is available in Swagger UI.

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-----------|
| POST | `/api/v1/auth/token/` | Login (returns access + refresh token) |
| POST | `/api/v1/auth/token/refresh/` | Renew access token |
| GET | `/api/v1/auth/me/` | Authenticated user profile |
| GET | `/api/v1/accounts/` | List accounts (with filters and pagination) |
| GET | `/api/v1/accounts/{id}/` | Account detail |
| POST | `/api/v1/accounts/{id}/transition/` | Change account status |
| POST | `/api/v1/accounts/{id}/assign/` | Assign account to a collector |
| POST | `/api/v1/accounts/{id}/add_note/` | Add note to timeline |
| GET | `/api/v1/payments/` | List payments |
| POST | `/api/v1/payments/` | Record new payment |
| POST | `/api/v1/payments/{id}/refund/` | Refund payment |
| GET | `/api/v1/imports/` | List import jobs |
| GET | `/api/v1/analytics/dashboard/` | Dashboard KPIs |
| GET | `/api/v1/analytics/collectors/` | Collector performance |
| GET | `/api/v1/analytics/payments/trends/` | Payment trends |
| GET | `/api/v1/analytics/aging-report/` | Aging report |
| GET | `/api/v1/agencies/` | List agencies |
| GET | `/api/v1/collectors/` | List collectors |
| GET | `/api/v1/schema/` | OpenAPI 3.0 schema (JSON) |
| GET | `/api/v1/docs/` | Interactive Swagger UI |
| POST | `/api/v1/payments/webhook/stripe/` | Stripe webhook |

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

---

## Production Infrastructure

### AWS — Overview

```
┌──────────────────────────────────────────────────────────┐
│                        AWS Account                        │
│                                                           │
│  ┌─────────────────── VPC (10.0.0.0/16) ───────────────┐ │
│  │                                                       │ │
│  │  ┌── Public Subnets ──┐   ┌── Private Subnets ──┐   │ │
│  │  │  NAT Gateway       │   │  EKS Worker Nodes   │   │ │
│  │  │  ALB               │   │  RDS PostgreSQL     │   │ │
│  │  │                    │   │  ElastiCache Redis   │   │ │
│  │  └────────────────────┘   └──────────────────────┘   │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────┐  ┌──────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ ECR │  │  S3  │  │   Secrets   │  │  Route53/ACM  │  │
│  │     │  │      │  │   Manager   │  │  (DNS + SSL)  │  │
│  └─────┘  └──────┘  └─────────────┘  └───────────────┘  │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Terraform Modules

| Module | Responsibility |
|--------|-----------------|
| `networking` | VPC, subnets (public/private), NAT Gateway, Internet Gateway |
| `eks` | EKS cluster, node groups, addons (CoreDNS, VPC CNI, EBS CSI) |
| `database` | RDS PostgreSQL 16 (Multi-AZ in production) |
| `cache` | ElastiCache Redis 7 |
| `storage` | S3 bucket with lifecycle (90d → Glacier, 365d → delete) |
| `ecr` | Container registries for API and frontend |
| `iam` | IRSA roles (worker, API, ALB controller) |
| `secrets` | Secrets Manager (DB password, Django key, Stripe, SFTP) |
| `dns` | Route53 hosted zone + ACM wildcard certificate |

### Kubernetes (Helm Chart)

The `debtflow` Helm chart manages all components:

- **API Deployment** — Gunicorn (3 replicas in prod)
- **Worker Deployment** — Celery worker (2 replicas)
- **Beat Deployment** — Celery beat (1 replica)
- **Frontend Deployment** — Nginx serving SPA (2 replicas)
- **Ingress** — ALB with multi-path routing (/api → API, / → frontend)
- **HPA** — Auto-scaling 3-10 pods based on CPU (70%)
- **PDB** — Disruption budget (minimum 2 pods available)
- **Network Policies** — Network isolation per component
- **Service Accounts** — IRSA for per-pod AWS permissions
- **Migration Job** — Helm hook pre-upgrade for `manage.py migrate`
- **CronJobs** — Automatic VACUUM and audit cleanup

### CI/CD Pipeline

```
Developer → Push to main → CI Tests → Build Images → Push ECR → Deploy Staging
                                                                       │
                                              Tag v*.*.* ──────────────┘
                                                    │
                                              Build Images → Push ECR → Deploy Production
                                                                            │
                                                                      Health Check
                                                                       ├── OK → Done
                                                                       └── Fail → Auto Rollback
```

---

## Environments

| Environment | URL | Trigger | Resources |
|----------|-----|---------|----------|
| **Local** | localhost:3000 / :8000 | `docker compose up` | Everything local, demo data |
| **Staging** | staging.debtflow.example.com | Push to `main` | EKS min resources, 1 replica |
| **Production** | debtflow.example.com | Tag `v*.*.*` | EKS HA, HPA 3-10, Multi-AZ RDS |

---

## Metrics and Monitoring

| Tool | Local URL | Function |
|-----------|-----------|--------|
| **Prometheus** | localhost:9090 | Collects API metrics (requests, latency, errors) |
| **Grafana** | localhost:3001 | Visual dashboards (admin/admin) |
| **Django Metrics** | localhost:8000/metrics | Application Prometheus endpoint |
| **Health Check** | localhost:8000/health/ | API health verification |

---

## Competitive Differentiators

1. **Cloud-Native from day zero** — not a migrated monolith; it was designed for Kubernetes
2. **Multi-tenant** — a single installation serves multiple agencies with data isolation
3. **Strict State Machine** — prevents invalid transitions, ensures pipeline consistency
4. **API-First** — all functionality available via REST, enabling integrations
5. **Complete observability** — Prometheus + Grafana + audit trail from the first deploy
6. **Automated import** — SFTP polling eliminates manual data entry work
7. **Compliance-ready** — immutable audit trail, PII encryption, granular access control

---

## Future Roadmap

- [ ] Real-time notifications (WebSocket)
- [ ] Mobile app for field collectors
- [ ] Credit bureau integration (Equifax, TransUnion)
- [ ] Rules engine for automatic account prioritization
- [ ] Integrated dialer (VoIP/Twilio) with call recording
- [ ] Debtor portal (self-service for payment and negotiation)
- [ ] FDCPA/TCPA compliance module with automatic validations
- [ ] Machine Learning for payment propensity scoring
- [ ] Exportable reports (PDF/Excel) scheduled via email
- [ ] Multi-language (EN/ES/PT)

---

## Contact and Links

| Resource | Link |
|---------|------|
| **API Docs (local)** | http://localhost:8000/api/v1/docs/ |
| **Frontend (local)** | http://localhost:3000 |
| **Grafana (local)** | http://localhost:3001 |
| **Repository** | GitHub (private) |

---

*DebtFlow — Turning debt collection into technology.*
