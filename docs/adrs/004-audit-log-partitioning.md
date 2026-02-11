# ADR-004: Range Partition AuditLog Table by Month

**Date:** 2025-01-25

**Status:** Accepted

## Context

The `AuditLog` table records every significant action in the system — account
modifications, payment events, communication dispatch, user actions, and API
calls. This table is append-only and grows indefinitely.

Based on projected volumes:

- ~500K audit records per month in year one.
- ~2M audit records per month at projected year-two scale.
- Records are almost exclusively queried by time range (e.g., "show all actions
  on this account in the last 90 days").

Without intervention, a single unpartitioned table will degrade query performance,
make index maintenance expensive, and complicate data retention and archival.

## Decision

We will use **PostgreSQL native range partitioning** on the `AuditLog` table,
partitioned by the `created_at` timestamp column with **monthly partitions**.

Specifics:

- Parent table: `audit_log` (partitioned by `RANGE (created_at)`).
- Child partitions: `audit_log_2025_01`, `audit_log_2025_02`, etc.
- New partitions created automatically via a monthly Celery Beat task that runs
  on the 1st of each month, creating the next month's partition.
- **Retention policy:** 24 months of online data. Partitions older than 24 months
  are detached and archived to S3 (Parquet format) before being dropped.
- Indexes are created per-partition (account_id, action_type, created_at).

## Consequences

**Positive:**

- Queries filtered by time range are pruned to only the relevant partitions,
  maintaining consistent performance as data grows.
- Index maintenance (VACUUM, REINDEX) operates on smaller partition-level
  indexes rather than a single massive index.
- Archival is clean: detach a partition, export, drop. No row-level DELETE
  operations that cause table bloat.
- 24-month retention satisfies current regulatory requirements while keeping
  the active dataset manageable.

**Negative:**

- Queries without a `created_at` filter will scan all partitions — developers
  must be disciplined about including time range predicates.
- Partition management adds operational overhead (creation, monitoring,
  archival automation).
- Django ORM does not natively manage PostgreSQL partitions — partition DDL
  is handled via raw SQL migrations.

**Mitigations:**

- Django queryset manager on `AuditLog` that enforces a default `created_at`
  filter to prevent accidental full-table scans.
- Alerting on partition creation failures (if the Celery task does not run).
- Integration tests that validate partition routing on write and query pruning
  on read.
