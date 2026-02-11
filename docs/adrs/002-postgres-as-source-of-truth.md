# ADR-002: PostgreSQL as Single Source of Truth

**Date:** 2025-01-15

**Status:** Accepted

## Context

DebtFlow manages financial data — account balances, payment transactions, payment
plan schedules, and regulatory audit trails. Data integrity is non-negotiable.
Any inconsistency in account balances or payment records could result in
regulatory violations, incorrect collections, or financial loss.

We evaluated several approaches:

- **PostgreSQL only:** Single relational database as the canonical data store.
- **PostgreSQL + event store:** Append-only event log with materialized read models.
- **Multi-database:** Separate databases per domain (e.g., a document store for
  communications, relational for payments).

## Decision

We will use **PostgreSQL as the single source of truth** for all application data.
There will be no secondary canonical data stores. All writes go through PostgreSQL
transactions.

Specifically:

- All financial mutations (payments, balance adjustments, plan changes) occur
  within ACID transactions.
- No eventual consistency patterns for core data. If a write succeeds, it is
  immediately visible to all readers.
- Read replicas may be introduced later for reporting workloads, but the primary
  instance remains the sole write target.

## Consequences

**Positive:**

- Strong transactional guarantees eliminate an entire class of data consistency bugs.
- Single data store simplifies backup, restore, and disaster recovery procedures.
- Django ORM works natively with PostgreSQL — no adapter complexity.
- `SELECT ... FOR UPDATE` and advisory locks available for concurrency control
  on sensitive operations (e.g., double-payment prevention).
- Straightforward compliance story: one database to audit, one set of access
  controls to manage.

**Negative:**

- Vertical scaling limits may eventually be reached if write throughput grows
  significantly. Current projections indicate this is unlikely within 2 years.
- All read and write traffic converges on a single system, making the database
  the primary bottleneck and single point of failure.
- Some workloads (full-text search on communications, large file metadata) might
  be more naturally served by specialized stores.

**Mitigations:**

- Connection pooling via PgBouncer to manage connection limits.
- Read replicas for reporting and analytics queries when needed.
- PostgreSQL full-text search (`tsvector`) covers current search requirements
  without introducing Elasticsearch.
- RDS Multi-AZ deployment for high availability.
