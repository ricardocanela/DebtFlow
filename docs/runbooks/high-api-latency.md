# Runbook: High API Latency

**Severity:** P2 (P1 if latency exceeds 10s or error rate spikes above 5%)
**Service:** DebtFlow API (Django REST Framework / Gunicorn)
**Last updated:** 2026-02-11

---

## Overview

The DebtFlow API is a Django REST Framework application served by Gunicorn behind a load balancer. API endpoints interact heavily with PostgreSQL (accounts, payments, analytics) and Redis (caching, circuit breaker state, Celery broker). High latency typically manifests as slow database queries, connection pool exhaustion, missing database indexes, or N+1 query patterns in serializers.

Key tables involved: `accounts_account`, `accounts_debtor`, `payments_payment`, `integrations_sftpimportjob`, `accounts_activity`.

---

## Symptoms

- API response times exceed the 200ms p95 baseline (visible in Grafana or Prometheus metrics via `django_prometheus`)
- Users report slow page loads on the DebtFlow frontend (`https://debtflow.example.com`)
- Sentry alerts for increased transaction durations
- Prometheus metric `django_http_requests_latency_seconds_by_view_method` shows elevated values
- Celery tasks (`process_payment`, `reconcile_payments`) timing out due to database contention
- HTTP 504 Gateway Timeout errors from the load balancer
- Gunicorn workers appear busy/stuck (`gunicorn.workers.alive` gauge dropping)

---

## Investigation Steps

### Step 1: Confirm the Scope of the Problem

Check if latency is isolated to specific endpoints or system-wide.

**Grafana Dashboard:**
Open the DebtFlow API dashboard and check:
- `django_http_requests_latency_seconds_by_view_method` broken down by view name
- Look for specific views: `AccountViewSet`, `PaymentViewSet`, `AnalyticsView`

**From the application server:**
```bash
# Check Gunicorn worker status
ps aux | grep gunicorn | grep -v grep

# Check active request count (if using Prometheus endpoint)
curl -s http://localhost:8000/metrics | grep django_http_requests_total

# Look at recent slow requests in the application logs
journalctl -u debtflow-api --since "30 minutes ago" | grep -i "slow\|timeout\|latency"
```

### Step 2: Check Database Performance

**Connect to PostgreSQL and check for slow queries:**

```sql
-- Active queries running longer than 5 seconds
SELECT
    pid,
    now() - query_start AS duration,
    state,
    left(query, 120) AS query_preview,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - query_start > interval '5 seconds'
  AND datname = 'debtflow'
ORDER BY duration DESC;
```

**Check pg_stat_statements for top slow queries (requires pg_stat_statements extension):**

```sql
-- Top 20 queries by total time
SELECT
    left(query, 100) AS query,
    calls,
    round(total_exec_time::numeric, 2) AS total_time_ms,
    round(mean_exec_time::numeric, 2) AS mean_time_ms,
    round(max_exec_time::numeric, 2) AS max_time_ms,
    rows
FROM pg_stat_statements
WHERE dbname = 'debtflow'
ORDER BY mean_exec_time DESC
LIMIT 20;
```

**Check for lock contention:**

```sql
-- Blocked queries waiting on locks
SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query,
    now() - blocked.query_start AS wait_duration
FROM pg_stat_activity blocked
JOIN pg_locks blocked_locks ON blocked.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocked_locks.locktype = blocking_locks.locktype
    AND blocked_locks.relation = blocking_locks.relation
    AND blocked_locks.pid != blocking_locks.pid
JOIN pg_stat_activity blocking ON blocking_locks.pid = blocking.pid
WHERE NOT blocked_locks.granted;
```

### Step 3: Identify N+1 Query Patterns

Common N+1 sources in DebtFlow based on the models:

- `AccountViewSet` fetching accounts without `select_related('agency', 'debtor', 'assigned_to')`
- `PaymentViewSet` fetching payments without `select_related('account', 'processor')`
- `Activity` queries on account detail views without `prefetch_related('activities')`

**Enable Django query logging temporarily:**

```bash
# Set Django log level for DB queries (on the application server)
# In Django shell or by setting the env variable:
DJANGO_LOG_LEVEL=DEBUG

# Or use django-debug-toolbar / django-silk in staging
```

**Check with Django shell:**

```python
# Connect to Django shell
python manage.py shell

from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True  # Temporarily enable query logging
reset_queries()

# Simulate the slow endpoint
from apps.accounts.models import Account
accounts = list(Account.objects.filter(status='new')[:50])
for a in accounts:
    _ = a.agency.name        # N+1 if no select_related
    _ = a.debtor.full_name   # N+1 if no select_related

print(f"Total queries: {len(connection.queries)}")
for q in connection.queries:
    print(f"  {q['time']}s: {q['sql'][:100]}")
```

### Step 4: Run EXPLAIN ANALYZE on Suspect Queries

**For account listing (the most common endpoint):**

```sql
-- Account listing query used by AccountViewSet
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT a.*, d.full_name, d.external_ref
FROM accounts_account a
JOIN accounts_debtor d ON a.debtor_id = d.id
WHERE a.agency_id = '<agency-uuid>'
  AND a.status IN ('new', 'assigned')
ORDER BY a.created_at DESC
LIMIT 50;
```

**For payment history queries:**

```sql
-- Payment listing with account join
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT p.*
FROM payments_payment p
WHERE p.account_id = '<account-uuid>'
  AND p.status = 'completed'
ORDER BY p.created_at DESC;
```

**What to look for in EXPLAIN output:**
- `Seq Scan` on large tables (should be `Index Scan` or `Index Only Scan`)
- `Nested Loop` with high row estimates (potential N+1 at DB level)
- `Sort` operations not using an index (external sorts are expensive)
- `Buffers: shared read` being very high (cold cache, data not in memory)

### Step 5: Check Connection Pool Status

```sql
-- Current connection count by state
SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = 'debtflow'
GROUP BY state
ORDER BY count DESC;

-- Check against max_connections
SHOW max_connections;
```

**If using PgBouncer:**

```bash
# Connect to PgBouncer admin console
psql -h localhost -p 6432 -U pgbouncer pgbouncer

# Check pool status
SHOW POOLS;
SHOW CLIENTS;
SHOW SERVERS;
SHOW STATS;
```

### Step 6: Check Redis Latency

Redis is used for caching (circuit breaker, idempotency keys) and as Celery broker.

```bash
# Check Redis latency
redis-cli -u redis://localhost:6379/0 --latency

# Check Redis memory usage
redis-cli -u redis://localhost:6379/0 INFO memory

# Check number of connected clients
redis-cli -u redis://localhost:6379/0 INFO clients

# Check slow log
redis-cli -u redis://localhost:6379/0 SLOWLOG GET 10
```

### Step 7: Check Application Server Resources

```bash
# CPU and memory on the API server
top -b -n 1 | head -20

# Check Gunicorn worker count and memory
ps aux | grep gunicorn | awk '{print $2, $3, $4, $11}'

# Check disk I/O (relevant for temp file operations during SFTP imports)
iostat -x 1 3

# Check network connections
ss -s
ss -tnp | grep :8000 | wc -l
```

---

## Resolution

### Immediate Mitigation

**Kill long-running queries (if they are causing cascading slowness):**

```sql
-- Cancel a specific query (graceful)
SELECT pg_cancel_backend(<pid>);

-- Terminate a specific connection (forceful — use as last resort)
SELECT pg_terminate_backend(<pid>);
```

**Scale Gunicorn workers if CPU is available:**

```bash
# Send TTIN signal to master to add a worker
kill -TTIN $(cat /var/run/gunicorn/debtflow.pid)

# Or restart with more workers
gunicorn config.wsgi:application --workers 8 --timeout 120
```

### Fix Missing Indexes

If EXPLAIN ANALYZE shows sequential scans on common query patterns:

```sql
-- Example: If filtering payments by status + date is slow
CREATE INDEX CONCURRENTLY idx_payment_status_created
ON payments_payment (status, created_at DESC);

-- Example: If account lookups by external_ref are slow
-- (This should already exist per the model, but verify)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_account_external_ref
ON accounts_account (external_ref);

-- Example: If activity timeline queries are slow
CREATE INDEX CONCURRENTLY idx_activity_account_created
ON accounts_activity (account_id, created_at DESC);
```

### Fix N+1 Queries

Update the viewsets/serializers to use `select_related` and `prefetch_related`:

```python
# In apps/accounts/views.py — AccountViewSet.get_queryset()
def get_queryset(self):
    return Account.objects.select_related(
        'agency', 'debtor', 'assigned_to', 'assigned_to__user'
    ).prefetch_related(
        'activities', 'payments'
    )

# In apps/payments/views.py — PaymentViewSet.get_queryset()
def get_queryset(self):
    return Payment.objects.select_related(
        'account', 'account__debtor', 'processor'
    )
```

### Fix Connection Pool Exhaustion

If connections are near `max_connections`:

```python
# In config/settings/base.py — set CONN_MAX_AGE to reuse connections
DATABASES = {
    "default": {
        # ... existing config ...
        "CONN_MAX_AGE": 600,  # Reuse connections for 10 minutes
    }
}
```

If PgBouncer is in use, ensure `pool_mode = transaction` and `max_client_conn` is appropriately sized.

### Tune PostgreSQL for Better Performance

```sql
-- Check if autovacuum is keeping up
SELECT
    relname,
    n_dead_tup,
    n_live_tup,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC
LIMIT 10;

-- If tables have excessive dead tuples, run manual vacuum
VACUUM ANALYZE accounts_account;
VACUUM ANALYZE payments_payment;
VACUUM ANALYZE accounts_activity;
```

---

## Prevention

1. **Query monitoring:** Enable `pg_stat_statements` in production and set up Grafana dashboards to alert on queries with mean execution time above 100ms.

2. **N+1 detection:** Add `nplusone` or `django-query-inspector` to the staging environment to catch N+1 patterns before they reach production.

3. **Load testing:** Run periodic load tests against staging with realistic data volumes (the `accounts_account` table can grow to millions of rows) to catch performance regressions.

4. **Index review:** Before each release, review new migrations for queries that may need indexes. Use `django-extensions` `show_urls` and `shell_plus` to audit query patterns.

5. **Connection pooling:** Deploy PgBouncer in front of PostgreSQL in production. Configure `CONN_MAX_AGE = 0` in Django when using PgBouncer in transaction pooling mode (PgBouncer manages the pool, not Django).

6. **Celery isolation:** Ensure Celery workers (`process_payment`, `sftp_poll_all_agencies`, `reconcile_payments`) use a separate database connection pool or PgBouncer pool to prevent worker queries from starving API connections.

7. **Sentry performance monitoring:** The Sentry integration (configured in `config/settings/production.py` with `traces_sample_rate=0.1`) provides transaction-level performance data. Review the Sentry Performance dashboard weekly.

8. **Pagination enforcement:** The DRF configuration uses `CursorPagination` with `PAGE_SIZE = 50`. Ensure no custom endpoints bypass pagination on large tables.

9. **Read replicas:** For heavy analytics queries (`apps/analytics`), consider routing read traffic to a PostgreSQL read replica using Django database routers.
