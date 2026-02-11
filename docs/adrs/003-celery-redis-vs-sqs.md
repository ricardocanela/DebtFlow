# ADR-003: Celery + Redis as Broker, SQS as Dead Letter Queue

**Date:** 2025-01-20

**Status:** Accepted

## Context

DebtFlow requires asynchronous task processing for several workloads:

- File ingestion and parsing (CSV/Excel processing).
- Payment processor webhook handling and retries.
- Communication dispatch (email, SMS, letter generation).
- Scheduled payment plan evaluations.

We evaluated three broker configurations for Celery:

- **Redis as broker:** Low latency, well-supported by Celery, familiar to the team.
- **SQS as broker:** Fully managed, highly durable, but higher latency and
  limited Celery feature support (no result backend, no priority queues).
- **RabbitMQ as broker:** Feature-rich AMQP broker, but adds operational
  complexity the team is not staffed to manage.

## Decision

We will use **Celery with Redis as the primary message broker**. Amazon SQS will
serve exclusively as a **dead letter queue (DLQ)** for tasks that exhaust all
retry attempts.

Configuration:

- Redis (ElastiCache) as the Celery broker and result backend.
- Task retries with exponential backoff handled within Celery.
- After max retries are exhausted, failed tasks are forwarded to an SQS DLQ
  for manual inspection and replay.
- Celery Beat for periodic task scheduling (payment plan evaluations, SFTP polling).

## Consequences

**Positive:**

- Sub-millisecond broker latency keeps task dispatch fast, critical for
  user-facing operations that trigger background work.
- Full Celery feature set available: task priorities, result backend, canvas
  workflows (chains, chords), ETA scheduling.
- Django + Celery is a well-documented, battle-tested combination — large
  ecosystem of resources and community support.
- SQS DLQ provides durable, inspectable storage for failed tasks without
  adding SQS complexity to the hot path.

**Negative:**

- Redis is an in-memory store. Broker data is lost if the Redis instance
  fails before tasks are consumed. This is acceptable because tasks are
  generally idempotent and retriable.
- Redis requires operational attention (memory limits, eviction policies,
  persistence configuration).
- Two messaging systems (Redis + SQS) to maintain instead of one.

**Mitigations:**

- ElastiCache Multi-AZ with automatic failover for Redis high availability.
- All tasks designed to be idempotent — safe to re-enqueue after broker failure.
- CloudWatch alarms on SQS DLQ depth to alert on elevated failure rates.
- Redis memory and connection metrics monitored via Datadog.
