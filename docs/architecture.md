# DebtFlow — System Architecture

## Overview

DebtFlow follows a **modular monolith architecture with async workers**. This design is appropriate for a small team (9 people) and avoids the operational complexity of microservices while maintaining clear module boundaries.

## Components

| Component | Technology | Responsibility | Replicas |
|---|---|---|---|
| API Server | Django 5.1 + DRF + Gunicorn | REST API, authentication, business logic | 3 (HPA) |
| Celery Worker | Celery 5 + Redis broker | Async tasks: SFTP import, payments, reports | 2 (HPA) |
| Celery Beat | Celery Beat | Scheduler: SFTP polling, cleanup, reports | 1 |
| Database | PostgreSQL 16 (RDS) | Transactional data, partitioned tables | Multi-AZ |
| Cache | Redis 7 (ElastiCache) | Session cache, broker, rate limiting | Cluster |
| Object Storage | AWS S3 | SFTP files, exports, backups | N/A |
| Monitoring | Prometheus + Grafana | Metrics, dashboards, alerts | 1 each |

## Data Flow

### Payment Processing
1. API receives payment request with idempotency key
2. Redis checks for duplicate (24h TTL)
3. Payment created as `pending` in DB
4. Stripe API called with circuit breaker protection
5. On success: status → `completed`, balance updated atomically
6. Webhook confirms asynchronously

### SFTP Import
1. Celery Beat triggers polling every 15 minutes
2. Paramiko connects to client SFTP servers
3. CSV files downloaded, backed up to S3
4. Pydantic validates each row
5. Batch insert (1000 records/transaction)
6. Errors isolated per row — one bad record doesn't block the batch

## Key Design Decisions

See [ADRs](adrs/) for detailed rationale on each architectural choice.

## Database Schema

- **Agency** → has many **Accounts**, **Collectors**
- **Account** → belongs to **Agency**, **Debtor**; has many **Payments**, **Activities**
- **Payment** → belongs to **Account**, **PaymentProcessor**
- **AuditLog** — generic via ContentType, partitioned by month

## Security

- JWT authentication with 15-minute access tokens
- Role-based access: agency_admin, collector, readonly
- Object-level permissions: collectors only see their assigned accounts
- Stripe webhook HMAC-SHA256 validation
- All secrets via environment variables (never in code)
