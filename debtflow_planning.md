# 🏦 DEBTFLOW — Development Planning Document

## Debt Collection Management Platform

**Portfolio Project | Stack: Django, DRF, PostgreSQL, Celery, Redis, Docker, Kubernetes, Helm, Terraform, GitHub Actions, Prometheus, Grafana**

**Ricardo Lima Canela** — github.com/ricardocanela/debtflow

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Data Modeling (PostgreSQL)](#3-data-modeling-postgresql)
4. [REST API — Endpoint Specification](#4-rest-api--endpoint-specification)
5. [External Integrations](#5-external-integrations)
6. [Containerization & Orchestration](#6-containerization--orchestration)
7. [Infrastructure as Code (Terraform)](#7-infrastructure-as-code-terraform)
8. [CI/CD Pipeline (GitHub Actions)](#8-cicd-pipeline-github-actions)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Repository Structure](#10-repository-structure)
11. [Testing Strategy](#11-testing-strategy)
12. [Implementation Timeline](#12-implementation-timeline)
13. [Quality Checklist](#13-quality-checklist)

---

## 1. Project Overview

### 1.1 What is DebtFlow

DebtFlow is a **backend management platform for debt collection agencies**. It functions as a specialized CRM that tracks delinquent accounts (instead of sales leads), with payment processor integrations and data ingestion via SFTP.

The project directly mirrors the Aktos product, demonstrating full mastery of the tech stack and business domain.

### 1.2 Why This Project

Every technical decision in DebtFlow maps directly to a requirement from the Staff Backend Engineer role at Aktos:

| Job Requirement | DebtFlow Implementation | Priority |
|---|---|---|
| Python/Django + DRF (Required) | Entire backend in Django 5.1 + DRF with ViewSets, Serializers, Permissions | **CRITICAL** |
| Python + DB Performance (Required) | Composite indexes, partitioning, EXPLAIN docs, connection pooling | **CRITICAL** |
| API Integrations (Required) | Stripe payment gateway: webhooks, idempotency, retry, circuit breaker | **CRITICAL** |
| SFTP Integrations (Required) | SFTP polling with paramiko, CSV parser, batch import, error tracking | **CRITICAL** |
| Feature Development (Required) | CRUD, workflow engine, audit trail, analytics dashboard | **CRITICAL** |
| Docker | Multi-stage Dockerfile, docker-compose for local dev | HIGH |
| Kubernetes / EKS | K8s manifests: Deployment, HPA, PDB, Ingress, CronJob | HIGH |
| Helm | Custom chart with per-environment values | HIGH |
| Terraform | Modules: VPC, EKS, RDS, ElastiCache, S3, SQS | HIGH |
| GitHub Actions | CI/CD: lint, test, build, deploy staging, deploy prod | HIGH |
| Redis | Cache, Celery broker, rate limiting, idempotency store | HIGH |
| Postgres monitoring | pg_stat_statements, index analysis, vacuum monitoring | HIGH |
| Monitoring/Alerting | Prometheus + Grafana dashboards + Alertmanager rules | HIGH |
| CI pipelines | GitHub Actions with matrix testing, coverage gates | HIGH |
| On-call/Runbooks | Documented runbooks for common incidents | HIGH |

---

## 2. System Architecture

### 2.1 Component Diagram

The system follows a **modular monolith architecture with async workers**, appropriate for a small team like Aktos (9 people):

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
  │ Pod (x3)     │           │ Pod (x3)      │
  │ • DRF        │           │ • DRF         │
  │ • Gunicorn   │           │ • Gunicorn    │
  └──────┬──────┘           └───────┬───────┘
         │                           │
    ┌────▼───┬────┬─────────┬───────▼──┐
    │        │    │         │          │
  ┌─▼──┐  ┌─▼─┐  ┌─▼─┐  ┌──▼─┐  ┌───▼───┐
  │PgSQL│  │Red│  │ S3│  │SQS │  │Celery │
  │ RDS │  │is │  │   │  │DLQ │  │Worker │
  └─────┘  └───┘  └───┘  └────┘  │Pods(2)│
                                  └───┬───┘
                                      │
                                  ┌───▼───┐
                                  │Celery │
                                  │ Beat  │
                                  │Pod(1) │
                                  └───────┘

  ┌────────────┐     ┌──────────┐
  │ Prometheus  │────▶│ Grafana  │
  └────────────┘     └──────────┘
```

### 2.2 Components & Responsibilities

| Component | Technology | Responsibility | Replicas |
|---|---|---|---|
| API Server | Django 5.1 + DRF + Gunicorn | REST API, authentication, business logic, webhooks | 3 (HPA) |
| Celery Worker | Celery 5 + Redis broker | Async tasks: SFTP import, payment reconciliation, emails, reports | 2 (HPA) |
| Celery Beat | Celery Beat | Scheduler: SFTP polling (15min), cleanup jobs, report generation | 1 |
| Database | PostgreSQL 16 (RDS) | Transactional data, partitioned tables, read replicas | Multi-AZ |
| Cache | Redis 7 (ElastiCache) | Session cache, Celery broker, rate limiting, idempotency keys | Cluster |
| Object Storage | AWS S3 | SFTP files, exports, receipts, backups | N/A |
| Dead Letter Queue | AWS SQS | Failed webhooks, retryable errors | N/A |
| Monitoring | Prometheus + Grafana | Application, infrastructure, and business metrics + dashboards + alerts | 1 each |

### 2.3 Architecture Decision Records (ADRs)

Each decision will be documented as an ADR in the repository:

| ADR | Decision | Rationale |
|---|---|---|
| ADR-001 | Modular monolith vs microservices | 9-person team — a monolith with separate Django apps is more productive and easier to debug. Microservices add unnecessary complexity at this stage. |
| ADR-002 | PostgreSQL as single source of truth | Transactional consistency is critical for financial data. No eventual consistency. |
| ADR-003 | Celery + Redis vs native SQS | Celery offers better DX with Django. Redis as broker is faster. SQS used only as DLQ. |
| ADR-004 | Range partitioning on AuditLog | Audit table grows indefinitely. Monthly range partitions allow fast historical queries and easy archival. |
| ADR-005 | Helm charts vs Kustomize | Helm allows templating with per-environment values, dependency management, and pre-deploy migration hooks. |
| ADR-006 | Terraform workspaces per environment | Reuse modules with different variables for staging/prod. Remote state with S3 + DynamoDB lock. |
| ADR-007 | SFTP polling vs push model | Debt collection agency clients typically deposit files on SFTP servers. Polling is the industry standard. |
| ADR-008 | Stripe as mock payment processor | Stripe has excellent documentation and sandbox. Simulates the type of integration Aktos does with real payment processors. |

---

## 3. Data Modeling (PostgreSQL)

The schema is designed for a financial system with high data volume, compliance requirements, and complex analytical queries.

### 3.1 Entity-Relationship Diagram

```
  ┌──────────┐       ┌───────────┐       ┌────────┐
  │  Agency   │1────N│  Account   │N────1│ Debtor  │
  └──────────┘       └───────────┘       └────────┘
       │1                 │1  │1
       │N                 │N  │N
  ┌───────────┐     ┌─────┐ ┌──────────┐
  │ Collector  │     │Pay- │ │ Activity  │
  └───────────┘     │ment │ └──────────┘
       │1           └──┬──┘
       │N              │N
  ┌───────────┐   ┌────┴──────┐
  │  Account   │   │ Payment   │
  │ (assigned) │   │ Processor │
  └───────────┘   └───────────┘

  ┌───────────────┐     ┌────────────┐
  │ SFTPImportJob  │1──N│  Imported   │
  └───────────────┘     │  Record    │
                        └────────────┘

  ┌────────────┐
  │  AuditLog   │  (generic via ContentType)
  │ partitioned │
  │  by month   │
  └────────────┘
```

### 3.2 Model Specifications

#### Model: Agency

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUIDField | PK, default=uuid4 | Unique identifier |
| name | CharField(255) | unique, indexed | Agency name |
| license_number | CharField(50) | unique, nullable | License number (compliance) |
| settings | JSONField | default={} | Customizable settings (timezone, currency, etc.) |
| is_active | BooleanField | default=True | Soft delete flag |
| created_at | DateTimeField | auto_now_add | Creation timestamp |
| updated_at | DateTimeField | auto_now | Last update timestamp |

#### Model: Debtor

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUIDField | PK, default=uuid4 | Unique identifier |
| external_ref | CharField(100) | unique, indexed | External ID (from client via SFTP) |
| full_name | CharField(255) | indexed | Debtor's full name |
| ssn_last4 | CharField(4) | encrypted at rest | Last 4 digits SSN (compliance) |
| email | EmailField | nullable | Debtor's email |
| phone | CharField(20) | nullable | Phone number |
| address_line1 | CharField(255) | nullable | Address line 1 |
| address_city | CharField(100) | nullable | City |
| address_state | CharField(2) | nullable | State |
| address_zip | CharField(10) | nullable | ZIP code |
| created_at | DateTimeField | auto_now_add | Creation timestamp |

#### Model: Account (Primary Table)

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUIDField | PK, default=uuid4 | Unique identifier |
| agency | ForeignKey(Agency) | on_delete=CASCADE, indexed | Owning agency |
| debtor | ForeignKey(Debtor) | on_delete=PROTECT, indexed | Associated debtor |
| assigned_to | ForeignKey(Collector) | nullable, on_delete=SET_NULL | Assigned collector |
| external_ref | CharField(100) | unique, indexed | External reference (from SFTP import) |
| original_amount | DecimalField(12,2) | not null | Original debt amount |
| current_balance | DecimalField(12,2) | not null | Current balance |
| status | CharField(20) | choices, indexed | Workflow status |
| priority | IntegerField | default=0, indexed | Collection priority |
| due_date | DateField | nullable | Original due date |
| last_contact_at | DateTimeField | nullable | Last debtor contact |
| created_at | DateTimeField | auto_now_add, indexed | Import date |
| updated_at | DateTimeField | auto_now | Last update |

**Status Workflow:** `new → assigned → in_contact → negotiating → payment_plan → settled → closed | disputed`

#### Model: Collector

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUIDField | PK, default=uuid4 | Unique identifier |
| user | OneToOneField(User) | on_delete=CASCADE | Associated Django user |
| agency | ForeignKey(Agency) | on_delete=CASCADE | Collector's agency |
| commission_rate | DecimalField(5,4) | default=0.10 | Commission rate (10%) |
| is_active | BooleanField | default=True | Active in system |
| max_accounts | IntegerField | default=200 | Simultaneous account limit |

#### Model: Payment

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUIDField | PK, default=uuid4 | Unique identifier |
| account | ForeignKey(Account) | on_delete=PROTECT, indexed | Associated account |
| processor | ForeignKey(PaymentProcessor) | on_delete=PROTECT | Processor used |
| amount | DecimalField(12,2) | not null | Payment amount |
| payment_method | CharField(20) | choices | card, bank_transfer, check, cash |
| status | CharField(20) | choices, indexed | pending, completed, failed, refunded |
| processor_ref | CharField(255) | unique, nullable | Transaction ID at processor |
| idempotency_key | CharField(64) | unique | Idempotency key |
| metadata | JSONField | default={} | Additional processor data |
| created_at | DateTimeField | auto_now_add, indexed | Payment timestamp |

#### Model: PaymentProcessor

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUIDField | PK | Unique identifier |
| name | CharField(100) | unique | Name (e.g., Stripe, Square) |
| slug | SlugField | unique | URL-safe identifier |
| api_base_url | URLField | — | Base API URL |
| api_key_encrypted | TextField | encrypted | API key (encrypted with Fernet) |
| webhook_secret | TextField | encrypted | Secret for webhook validation |
| is_active | BooleanField | default=True | Enabled for use |

#### Model: SFTPImportJob

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUIDField | PK | Unique identifier |
| agency | ForeignKey(Agency) | on_delete=CASCADE | Client agency |
| source_host | CharField(255) | — | Client SFTP host |
| file_name | CharField(255) | — | Processed file name |
| file_path_s3 | CharField(500) | nullable | S3 path after upload |
| status | CharField(20) | choices, indexed | pending, processing, completed, failed |
| total_records | IntegerField | default=0 | Total records in file |
| processed_ok | IntegerField | default=0 | Successfully imported records |
| processed_errors | IntegerField | default=0 | Records with errors |
| error_details | JSONField | default=[] | Error list by line number |
| started_at | DateTimeField | nullable | Processing start time |
| completed_at | DateTimeField | nullable | Processing end time |
| created_at | DateTimeField | auto_now_add | Job creation timestamp |

#### Model: AuditLog (Partitioned by Month)

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | BigAutoField | PK | Sequential ID |
| user | ForeignKey(User) | nullable, on_delete=SET_NULL | User who performed the action |
| action | CharField(20) | choices | create, update, delete, view, export |
| content_type | ForeignKey(ContentType) | — | Affected model type |
| object_id | UUIDField | indexed | Affected object ID |
| changes | JSONField | default={} | Diff of changes (old/new values) |
| ip_address | GenericIPAddressField | nullable | Request IP |
| created_at | DateTimeField | auto_now_add, indexed | Action timestamp |

**Partitioning:** RANGE by `created_at` (monthly). Retention: 24 months online, then archive to S3.

### 3.3 Indexing Strategy

Each index is planned for real system queries. All will be validated with `EXPLAIN (ANALYZE, BUFFERS)` and documented.

| Table | Index | Type | Query It Serves |
|---|---|---|---|
| Account | `(agency_id, status, created_at)` | Composite B-tree | Main listing: accounts by agency filtered by status |
| Account | `(agency_id, assigned_to_id)` | Composite B-tree | Accounts by collector within an agency |
| Account | `(status) WHERE status IN ('new','assigned')` | Partial index | Dashboard: pending accounts (most frequent query) |
| Account | `(external_ref)` | B-tree unique | Deduplication during SFTP import |
| Payment | `(account_id, created_at)` | Composite B-tree | Payment history for an account |
| Payment | `(status, created_at)` | Composite B-tree | Payment reports by period |
| Payment | `(idempotency_key)` | B-tree unique | Idempotency check |
| AuditLog | `(content_type_id, object_id, created_at)` | Composite B-tree | Activity timeline for an object |
| Debtor | `(external_ref)` | B-tree unique | Fast lookup during SFTP import |
| Debtor | `(full_name) gin_trgm_ops` | GIN trigram | Partial name search (LIKE/ILIKE) |
| SFTPImportJob | `(agency_id, status, created_at)` | Composite B-tree | Import dashboard by agency |

---

## 4. REST API — Endpoint Specification

All APIs follow REST conventions with URL-based versioning (`/api/v1/`). Auto-generated documentation via drf-spectacular (OpenAPI 3.0).

### 4.1 Authentication & Authorization

| Aspect | Implementation |
|---|---|
| Auth method | JWT (djangorestframework-simplejwt) with refresh tokens |
| Token lifetime | Access token: 15min TTL. Refresh token: 7 days, rotate on use |
| Roles | agency_admin, collector, readonly (via Django groups) |
| Object permissions | Collector can only see accounts from their agency assigned to them |
| Throttling | Anon: 100/hour. Auth: 1000/hour. Webhook: 5000/hour |

### 4.2 Detailed Endpoints

#### Accounts

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/accounts/` | Authenticated | List accounts with filters (status, collector, date range, amount range). Cursor-based pagination. |
| POST | `/api/v1/accounts/` | AgencyAdmin | Create new account manually |
| GET | `/api/v1/accounts/{id}/` | Authenticated | Detail with debtor, payments, notes inline (select_related + prefetch_related) |
| PATCH | `/api/v1/accounts/{id}/` | AgencyAdmin/Collector | Update fields allowed by role |
| POST | `/api/v1/accounts/{id}/assign/` | AgencyAdmin | Assign account to a collector. Changes status to 'assigned'. Creates Activity. |
| POST | `/api/v1/accounts/{id}/add_note/` | Authenticated | Add text note. Creates Activity in timeline. |
| GET | `/api/v1/accounts/{id}/timeline/` | Authenticated | Full activity timeline (notes, status changes, payments) |
| POST | `/api/v1/accounts/{id}/transition/` | Collector | Status transition with workflow validation (state machine) |
| GET | `/api/v1/accounts/export/` | AgencyAdmin | Async CSV export via Celery. Returns job ID for polling. |

#### Payments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/payments/` | Authenticated | Record payment. Generates idempotency key. Initiates Stripe charge. |
| GET | `/api/v1/payments/` | Authenticated | List payments with filters (account, status, date, amount) |
| GET | `/api/v1/payments/{id}/` | Authenticated | Payment detail with processor metadata |
| POST | `/api/v1/payments/webhook/stripe/` | Public (HMAC) | Stripe webhook receiver. Validates HMAC-SHA256 signature. |
| POST | `/api/v1/payments/{id}/refund/` | AgencyAdmin | Initiate refund on Stripe. Status → refunded. |

#### SFTP Imports

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/imports/` | AgencyAdmin | List import jobs with status, counters, timestamps |
| GET | `/api/v1/imports/{id}/` | AgencyAdmin | Job detail with error_details |
| POST | `/api/v1/imports/trigger/` | AgencyAdmin | Manual import trigger (outside normal schedule) |
| GET | `/api/v1/imports/{id}/errors/` | AgencyAdmin | Paginated error list with line number and reason |

#### Analytics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/analytics/dashboard/` | AgencyAdmin | KPIs: total collected, collection rate, avg days to settle, accounts by status |
| GET | `/api/v1/analytics/collectors/` | AgencyAdmin | Performance by collector: accounts, collected amount, success rate |
| GET | `/api/v1/analytics/payments/trends/` | AgencyAdmin | Payments by day/week/month with window functions |
| GET | `/api/v1/analytics/aging-report/` | AgencyAdmin | Aging buckets: 0-30, 31-60, 61-90, 90+ days |

---

## 5. External Integrations

### 5.1 Payment Processor (Stripe)

The Stripe integration simulates exactly the type of work Aktos does with payment processors.

#### Payment Flow

1. Collector creates payment via API with `idempotency_key`
2. Service layer validates amount, checks for duplicates via Redis (idempotency_key with 24h TTL)
3. Creates Payment with `status=pending` in DB
4. Sends charge to Stripe API with idempotency key
5. On success: updates Payment `status=completed`, updates Account balance
6. On transient failure: schedules retry via Celery (exponential backoff: 2s, 4s, 8s, max 3 retries)
7. On permanent failure: Payment `status=failed`, notifies via SQS DLQ

#### Webhook Receiver

| Aspect | Implementation |
|---|---|
| Endpoint | `POST /api/v1/payments/webhook/stripe/` (public, no auth) |
| Verification | HMAC-SHA256 of payload with PaymentProcessor's webhook_secret |
| Idempotency | Stripe event ID stored in Redis. Duplicate events are ignored. |
| Events handled | payment_intent.succeeded, payment_intent.failed, charge.refunded, charge.dispute.created |
| Processing | Sync for status update. Async (Celery) for reconciliation and notifications. |
| Retry handling | Stripe resends up to 3x. Our endpoint is idempotent, so reprocessing is safe. |
| Logging | Full payload logged to AuditLog with action='webhook_received' |

#### Circuit Breaker Pattern

To protect against Stripe API unavailability:

- State maintained in Redis: `closed` (normal), `open` (failing), `half-open` (testing)
- Opens after 5 failures within 60 seconds
- Attempts half-open after 30 seconds
- In open state: returns immediate error without calling API, schedules retry

### 5.2 SFTP Data Ingestion

The key differentiator of this project. Aktos explicitly requires SFTP integration experience.

#### Import Flow

1. Celery Beat fires `sftp_poll_all_agencies` task every 15 minutes
2. For each agency with SFTP config: connects via paramiko, lists new files
3. Downloads file to `/tmp`, uploads to S3 (backup)
4. Creates SFTPImportJob with `status=processing`
5. Parser identifies format (CSV or fixed-width) and validates schema with Pydantic
6. Batch processing: 1000 records per transaction
7. For each record: upsert Debtor (by external_ref), create/update Account
8. Errors isolated per row: a record with an error does not block the batch
9. On completion: updates SFTPImportJob with counters and `status=completed/failed`
10. Moves file to `/processed/` folder on SFTP server

#### CSV File Schema (example)

```csv
external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type
ACC-001,John Doe,1234,john@email.com,555-0100,1500.00,2024-01-15,Hospital X,medical
ACC-002,Jane Smith,5678,jane@email.com,555-0200,3200.50,2024-02-20,Bank Y,credit_card
```

#### Pydantic Validation

Each row is validated with a Pydantic model before insertion:

- `external_ref`: required, max 100 chars
- `original_amount`: positive Decimal
- `due_date`: ISO format (YYYY-MM-DD)
- `debtor_ssn_last4`: exactly 4 digits
- `email`: valid format or empty

Validation errors are collected in `error_details` on the SFTPImportJob with line number and reason.

---

## 6. Containerization & Orchestration

### 6.1 Docker

#### Dockerfile (Multi-stage)

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements/prod.txt .
RUN pip install --no-cache-dir -r prod.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
RUN adduser --disabled-password --no-create-home appuser
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
WORKDIR /app
COPY . .
USER appuser
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health/ || exit 1
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### docker-compose.yml (Local Dev)

Services: `api`, `worker`, `beat`, `postgres`, `redis`, `sftp-test-server`, `prometheus`, `grafana`

The `sftp-test-server` is an `atmoz/sftp` container to simulate the client SFTP in development.

### 6.2 Kubernetes Manifests

| Resource | File | Configuration | Purpose |
|---|---|---|---|
| Deployment (API) | api-deployment.yaml | 3 replicas, rolling update (maxSurge:1, maxUnavailable:0) | Zero-downtime deploys |
| Deployment (Worker) | worker-deployment.yaml | 2 replicas, resource limits (512Mi/500m) | Task processing |
| Deployment (Beat) | beat-deployment.yaml | 1 replica (singleton), leader election | Scheduled tasks |
| Service | api-service.yaml | ClusterIP, port 8000 | Internal service discovery |
| Ingress | ingress.yaml | AWS ALB, TLS via cert-manager, path-based routing | External access |
| HPA | api-hpa.yaml | min:2, max:10, CPU target 70%, custom: request latency | Auto-scaling |
| PDB | api-pdb.yaml | minAvailable: 2 | Protection against eviction |
| ConfigMap | configmap.yaml | DJANGO_SETTINGS_MODULE, DATABASE_HOST, REDIS_URL | Non-secret config |
| Secret | secret.yaml | DB password, API keys, JWT secret (sealed-secrets) | Sensitive data |
| CronJob | vacuum-cronjob.yaml | Weekly VACUUM ANALYZE on large tables | DB maintenance |
| CronJob | audit-cleanup.yaml | Monthly archive of old audit logs to S3 | Data lifecycle |
| NetworkPolicy | network-policy.yaml | Only API pods can reach DB, only workers reach Redis | Security |
| Job (pre-deploy) | migrate-job.yaml | Django migrate, runs before deployment via Helm hook | Schema migrations |

### 6.3 Helm Chart

Chart structure: `debtflow/`

- `Chart.yaml` — metadata, version, dependencies (redis, prometheus)
- `values.yaml` — defaults
- `values-staging.yaml` — staging overrides (1 replica, smaller resources)
- `values-production.yaml` — prod overrides (3 replicas, larger resources, real secrets)
- `templates/` — all K8s manifests with Go templating

Key parameterized values: `replicaCount`, `image.tag`, `resources.limits`, `ingress.host`, `database.host`, `redis.host`, `celery.concurrency`.

---

## 7. Infrastructure as Code (Terraform)

All AWS infrastructure provisioned via Terraform with remote state (S3 + DynamoDB lock) and workspaces per environment.

| Module | AWS Resources | Key Variables | Outputs |
|---|---|---|---|
| networking | VPC, 2 public subnets, 2 private subnets, NAT Gateway, Internet Gateway, Route Tables, Security Groups | vpc_cidr, azs, environment | vpc_id, private_subnet_ids, public_subnet_ids, sg_ids |
| eks | EKS Cluster, Managed Node Group (t3.medium), IAM Roles (cluster, node, IRSA), OIDC Provider | cluster_name, node_instance_type, node_min/max/desired | cluster_endpoint, cluster_ca, oidc_provider_arn |
| database | RDS PostgreSQL 16, Multi-AZ, Subnet Group, Parameter Group (shared_preload_libraries=pg_stat_statements), Automated Backups (7 days) | instance_class, allocated_storage, db_name | db_endpoint, db_port, db_name |
| cache | ElastiCache Redis 7, Replication Group, Subnet Group, Encryption at rest + in transit | node_type, num_cache_nodes | redis_endpoint, redis_port |
| storage | S3 Bucket (SFTP files), Lifecycle Policy (Glacier after 90 days), Encryption (AES-256), Versioning | bucket_name, retention_days | bucket_arn, bucket_name |

### Best Practices Implemented

- **Remote state:** S3 bucket with DynamoDB table for locking (prevents concurrent apply conflicts)
- **Workspaces:** `terraform workspace` for staging and production with shared modules
- **Reusable modules** with typed variables (string, number, list, map) and validation
- **`terraform plan`** as mandatory PR step via GitHub Actions
- **Sensitive outputs** marked as `sensitive = true`
- **Standardized tags** on all resources: Environment, Project, ManagedBy=terraform

---

## 8. CI/CD Pipeline (GitHub Actions)

### 8.1 CI Pipeline (Pull Request)

| Step | Tools | Success Criteria | Est. Time |
|---|---|---|---|
| Lint | ruff check + ruff format --check | Zero lint errors | ~15s |
| Type Check | mypy --strict (core modules) | Zero type errors | ~30s |
| Unit Tests | pytest -m 'not integration' --cov=80 | 100% pass, coverage ≥ 80% | ~2min |
| Integration Tests | pytest -m integration (with real Postgres via service container) | 100% pass | ~3min |
| Security Scan | bandit (code) + safety (deps) + trivy (container) | Zero high/critical | ~1min |
| Build Image | docker build --target runtime | Build succeeds | ~2min |

### 8.2 CD Pipeline (Deploy)

| Trigger | Action | Target | Approval |
|---|---|---|---|
| Merge to main | Build + Push image to ECR | ECR Registry | Automatic |
| Merge to main | `helm upgrade --install -f values-staging.yaml` | EKS Staging | Automatic |
| Tag `v*.*.*` | `helm upgrade --install -f values-production.yaml` | EKS Production | Manual (GitHub Environment Protection) |

### Technical Details

- **AWS auth:** OIDC federation (no static secret keys in GitHub)
- **ECR:** Push with tag = git SHA + latest
- **Helm hook pre-upgrade:** Django migrate Job
- **Post-deploy health check:** `curl /health/` with 5x retry
- **Automatic rollback:** if health check fails, `helm rollback`

---

## 9. Monitoring & Observability

### 9.1 Metrics (Prometheus + django-prometheus)

| Metric | Type | Labels | Purpose |
|---|---|---|---|
| `debtflow_http_requests_total` | Counter | method, endpoint, status_code | Request rate, error rate |
| `debtflow_http_request_duration_seconds` | Histogram | method, endpoint | Latency P50, P95, P99 |
| `debtflow_db_query_duration_seconds` | Histogram | query_name | Slow query detection |
| `debtflow_payment_total` | Counter | status, processor, method | Payment success/failure rate |
| `debtflow_sftp_import_records_total` | Counter | agency, status | Import volume and error rate |
| `debtflow_sftp_import_duration_seconds` | Histogram | agency | Import job duration |
| `debtflow_celery_task_duration_seconds` | Histogram | task_name, status | Task performance |
| `debtflow_active_accounts_gauge` | Gauge | agency, status | Business metric: accounts by status |

### 9.2 Grafana Dashboards

| Dashboard | Panels | Refresh |
|---|---|---|
| API Overview | Request rate (RPS), Error rate (%), P95 latency (ms), Top 10 slowest endpoints, Status code distribution | 30s |
| Database Health | Active connections, Query duration P95, Cache hit ratio, Replication lag, Table sizes, Vacuum status | 1min |
| Celery Workers | Tasks processed/min, Task duration by type, Queue depth, Worker utilization, Failed tasks | 30s |
| Business Metrics | Payments/hour, Total collected today/week/month, Import success rate, Active accounts by status, Collection rate | 5min |
| Infrastructure | Pod CPU/memory, Node utilization, PVC usage, Network I/O, HPA scaling events | 1min |

### 9.3 Alerts (Alertmanager)

| Alert | Condition | Severity | Action |
|---|---|---|---|
| HighApiLatency | P95 > 500ms for 5 minutes | Warning | Investigate slow queries, check DB connections |
| HighErrorRate | 5xx rate > 5% for 3 minutes | Critical | Page on-call, check logs, recent deploys |
| DatabaseConnectionsHigh | Connections > 80% of max | Warning | Check PgBouncer, connection leaks |
| CeleryQueueBacklog | Queue depth > 1000 for 10 minutes | Warning | Scale workers, check stuck tasks |
| SFTPImportFailed | Import job status=failed | Warning | Check error_details, contact client if file corrupted |
| PaymentProcessorDown | Circuit breaker open | Critical | Check Stripe status, hold payments |
| PodCrashLooping | Restart count > 3 in 10min | Critical | Check logs, OOM kills, config errors |
| DiskUsageHigh | PVC usage > 85% | Warning | Cleanup, expand volume, archive old data |

---

## 10. Repository Structure

```
debtflow/
├── apps/
│   ├── accounts/              # Agency, Debtor, Account, Collector models + API
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py           # ViewSets with @action decorators
│   │   ├── filters.py         # django-filter FilterSets
│   │   ├── permissions.py     # IsAgencyAdmin, IsCollector, IsAccountOwner
│   │   ├── services.py        # Business logic (assign, transition, etc.)
│   │   ├── tests/
│   │   │   ├── test_models.py
│   │   │   ├── test_api.py
│   │   │   ├── test_services.py
│   │   │   └── factories.py   # factory-boy factories
│   │   ├── migrations/
│   │   └── admin.py
│   │
│   ├── payments/              # Payment, PaymentProcessor models + API + Stripe
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py        # PaymentService, StripeClient, CircuitBreaker
│   │   ├── webhooks.py        # Stripe webhook handler
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── integrations/          # SFTP import/export
│   │   ├── models.py          # SFTPImportJob, ImportedRecord
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── sftp_client.py     # paramiko wrapper
│   │   ├── parsers.py         # CSV/fixed-width parsers + Pydantic validation
│   │   ├── importers.py       # Batch import logic
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── analytics/             # Dashboard endpoints (read-only)
│   │   ├── views.py           # Optimized queries with annotate/aggregate
│   │   ├── queries.py         # Raw SQL for complex reports
│   │   └── tests/
│   │
│   └── audit/                 # AuditLog model + middleware
│       ├── models.py          # Partitioned AuditLog
│       ├── middleware.py       # Auto-audit on model changes
│       └── migrations/
│
├── config/                    # Django settings
│   ├── settings/
│   │   ├── base.py            # Common settings
│   │   ├── local.py           # Dev (DEBUG=True, local DB)
│   │   ├── staging.py         # Staging (RDS, ElastiCache)
│   │   └── production.py      # Prod (strict security, Sentry)
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py              # Celery app config
│
├── tasks/                     # Celery tasks
│   ├── sftp_tasks.py          # sftp_poll_all_agencies, process_import_file
│   ├── payment_tasks.py       # process_payment, reconcile_payments
│   ├── report_tasks.py        # generate_export, send_report_email
│   └── maintenance.py         # vacuum_tables, archive_audit_logs
│
├── infra/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── networking/    # VPC, subnets, NAT, SGs
│   │   │   ├── eks/           # EKS cluster, node groups, IRSA
│   │   │   ├── database/      # RDS PostgreSQL
│   │   │   ├── cache/         # ElastiCache Redis
│   │   │   └── storage/       # S3 buckets
│   │   ├── environments/
│   │   │   ├── staging/       # terraform.tfvars for staging
│   │   │   └── production/    # terraform.tfvars for prod
│   │   ├── backend.tf         # S3 + DynamoDB remote state
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── helm/
│       └── debtflow/
│           ├── Chart.yaml
│           ├── values.yaml
│           ├── values-staging.yaml
│           ├── values-production.yaml
│           └── templates/
│               ├── api-deployment.yaml
│               ├── worker-deployment.yaml
│               ├── beat-deployment.yaml
│               ├── service.yaml
│               ├── ingress.yaml
│               ├── hpa.yaml
│               ├── pdb.yaml
│               ├── configmap.yaml
│               ├── secret.yaml
│               ├── migrate-job.yaml
│               ├── network-policy.yaml
│               └── cronjobs.yaml
│
├── docker/
│   ├── Dockerfile             # Multi-stage (builder + runtime)
│   ├── Dockerfile.worker      # Worker-specific
│   ├── docker-compose.yml     # Dev environment
│   ├── docker-compose.test.yml # CI environment
│   └── .dockerignore
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml             # Lint + Test + Build (PRs)
│   │   ├── cd-staging.yml     # Deploy to staging (merge to main)
│   │   ├── cd-production.yml  # Deploy to prod (tag v*)
│   │   └── terraform-plan.yml # TF plan on infra changes
│   └── CODEOWNERS
│
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml     # Scrape config
│   │   └── alert-rules.yml    # Alert rules
│   └── grafana/
│       ├── dashboards/
│       │   ├── api-overview.json
│       │   ├── db-health.json
│       │   ├── celery-workers.json
│       │   └── business-metrics.json
│       └── provisioning/
│
├── scripts/
│   ├── seed_data.py           # Fake data generation
│   ├── run_migrations.sh
│   └── sftp_test_upload.py    # Upload test files to SFTP
│
├── docs/
│   ├── architecture.md        # System architecture overview
│   ├── performance.md         # EXPLAIN outputs, optimization docs
│   ├── adrs/                  # Architecture Decision Records
│   │   ├── 001-monolith-vs-microservices.md
│   │   ├── 002-postgres-as-source-of-truth.md
│   │   ├── 003-celery-redis-vs-sqs.md
│   │   ├── 004-audit-log-partitioning.md
│   │   ├── 005-helm-vs-kustomize.md
│   │   ├── 006-terraform-workspaces.md
│   │   ├── 007-sftp-polling-vs-push.md
│   │   └── 008-stripe-as-mock-processor.md
│   ├── runbooks/
│   │   ├── high-api-latency.md
│   │   ├── database-connection-exhaustion.md
│   │   ├── sftp-import-failure.md
│   │   └── payment-processor-outage.md
│   └── api.md                 # API usage guide
│
├── requirements/
│   ├── base.txt
│   ├── local.txt              # Dev dependencies
│   ├── prod.txt
│   └── test.txt
│
├── manage.py
├── pyproject.toml             # ruff, mypy, pytest config
├── Makefile                   # make dev, make test, make lint, make deploy-staging
├── README.md
├── CONTRIBUTING.md
└── .env.example
```

---

## 11. Testing Strategy

| Type | Scope | Tools | Coverage Goal |
|---|---|---|---|
| Unit Tests | Models, services, serializers, parsers, utils | pytest, pytest-django, factory-boy, freezegun | 90%+ |
| Integration Tests | API endpoints end-to-end with real DB | pytest, DRF APIClient, docker postgres service | 80%+ |
| Webhook Tests | Stripe webhook receiver with real payloads | pytest, HMAC signature generation | 100% |
| SFTP Tests | Import pipeline with mocked SFTP server | pytest, paramiko mock, temp files | 90%+ |
| Performance Tests | Critical queries with EXPLAIN + benchmark | pytest-benchmark, django-debug-toolbar | Key queries |
| Load Tests | Critical endpoints under load (100 concurrent) | locust (script in locustfile.py) | P95 < 500ms |

### Critical Tests to Implement

1. Account list endpoint: 10K accounts, verify < 100ms with indexes
2. Payment webhook: verify HMAC validation rejects invalid signatures
3. Payment webhook: verify idempotency (same event ID processed once)
4. SFTP import: 5000 records, verify batch processing and error isolation
5. SFTP import: malformed CSV, verify graceful error handling
6. Account status transition: verify state machine rejects invalid transitions
7. Dashboard analytics: verify aggregations match raw data (consistency check)
8. Circuit breaker: verify opens after N failures, closes on recovery
9. Concurrent payments: verify no race condition on balance update (`select_for_update`)
10. Auth: verify collector cannot access accounts from another agency

---

## 12. Implementation Timeline

Plan: **6 weeks** (3-4 hours/day). Ordered so you have something functional at each phase.

### Phase 1: Foundation (Weeks 1-2)

| Day | Task | Deliverable |
|---|---|---|
| W1 D1 | Setup: Django project, pyproject.toml, Makefile, .env.example | `make dev` runs the empty project |
| W1 D2 | Docker: Multi-stage Dockerfile + docker-compose.yml (api, db, redis) | `docker compose up` works |
| W1 D3-4 | Models: Agency, Debtor, Account, Collector + migrations + admin | Models created with example fixtures |
| W1 D5 | Models: Payment, PaymentProcessor, SFTPImportJob, AuditLog | Complete schema migrated |
| W1 D6-7 | Indexes: create all planned indexes, test with EXPLAIN | docs/performance.md with initial outputs |
| W2 D1-2 | DRF: Serializers + ViewSets for Account (CRUD + actions) | Account API functional with filters |
| W2 D3 | DRF: Permissions (IsAgencyAdmin, IsCollector) + JWT auth | Complete auth, role-based access |
| W2 D4-5 | DRF: Payment endpoints + Debtor endpoints | Full API (without external integrations) |
| W2 D6-7 | Tests: unit + integration tests for all Phase 1 work | 80%+ coverage, CI green |

### Phase 2: Integrations (Weeks 3-4)

| Day | Task | Deliverable |
|---|---|---|
| W3 D1-2 | Celery setup: config, Redis broker, task base class with retry | Worker running in docker-compose |
| W3 D3-4 | Stripe integration: PaymentService, charge creation, idempotency | Payment functional with Stripe sandbox |
| W3 D5-6 | Stripe webhooks: receiver, HMAC validation, event processing | Webhook endpoint processing events |
| W3 D7 | Circuit breaker: implementation + Redis state management | Circuit breaker protecting Stripe calls |
| W4 D1-2 | SFTP client: paramiko wrapper, connection management | SFTP connection with test server functional |
| W4 D3-4 | SFTP import: CSV parser, Pydantic validation, batch importer | 5000-record import functional |
| W4 D5 | SFTP automation: Celery Beat polling + S3 backup + error tracking | Auto-import every 15min |
| W4 D6-7 | Tests: webhooks, SFTP import, circuit breaker, basic load test | 90%+ coverage on integrations |

### Phase 3: Analytics + Performance (Week 5)

| Day | Task | Deliverable |
|---|---|---|
| W5 D1-2 | Analytics: dashboard queries with annotate/aggregate + raw SQL | Analytics endpoints functional |
| W5 D3 | AuditLog: monthly partitioning + auto-audit middleware | Automatic audit trail on all changes |
| W5 D4-5 | Performance: EXPLAIN docs for all critical queries | docs/performance.md complete with before/after |
| W5 D6-7 | Account workflow: state machine with transition validation | Status transitions protected |

### Phase 4: DevOps & Infrastructure (Week 6)

| Day | Task | Deliverable |
|---|---|---|
| W6 D1 | GitHub Actions: CI pipeline (lint, test, build) | PR pipeline green |
| W6 D2 | Terraform: modules networking + database + cache + storage | AWS infra as code |
| W6 D3 | Terraform: module EKS + IRSA | Provisionable EKS cluster |
| W6 D4 | Helm: complete chart with templates and per-env values | `helm install` functional on minikube |
| W6 D5 | GitHub Actions: CD pipeline (build, push ECR, helm upgrade) | Automated deploy |
| W6 D6 | Monitoring: Prometheus config + django-prometheus + Grafana dashboards | Metrics collected and visualized |
| W6 D7 | Docs: README, ADRs, runbooks, CONTRIBUTING.md | Professional, documented repo |

---

## 13. Quality Checklist

Before putting this in the Aktos application form, verify each item:

### Code

- [ ] Ruff lint passes with zero errors
- [ ] Mypy type check passes on core modules
- [ ] Tests pass with 80%+ total coverage
- [ ] No hardcoded secrets (use .env.example)
- [ ] Docstrings on all public services and views
- [ ] Type hints on all public functions

### Repository

- [ ] Professional README.md with badges, diagram, quick start
- [ ] CONTRIBUTING.md with setup guide
- [ ] .env.example with all variables documented
- [ ] Makefile with targets: dev, test, lint, migrate, seed
- [ ] Atomic commits with conventional commits (feat:, fix:, docs:, infra:)
- [ ] At least 3 merged PRs (simulate real workflow)

### Documentation

- [ ] 8 ADRs written (one per architectural decision)
- [ ] docs/performance.md with real EXPLAIN outputs
- [ ] 4 runbooks for common incidents
- [ ] API documentation accessible at /api/v1/docs/

### Infrastructure

- [ ] Terraform modules with README in each module
- [ ] Helm chart that installs on minikube with `make helm-install`
- [ ] docker-compose.yml that brings everything up with `docker compose up`
- [ ] Functional CI pipeline on GitHub Actions

### Final Notes

The project **does not need to be deployed on AWS** (that would cost money). What matters is:

- **Clean, functional code** running locally with Docker
- **Terraform that COULD provision** (validated with `terraform plan`)
- **Helm that COULD deploy** (tested on minikube)
- **Documentation that shows Staff Engineer thinking**
- **Performance docs that demonstrate PostgreSQL proficiency**
- **Real integrations** (Stripe sandbox, SFTP test server)

---

*Let's build it!* 🚀
