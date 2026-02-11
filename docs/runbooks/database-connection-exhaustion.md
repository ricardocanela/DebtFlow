# Runbook: Database Connection Exhaustion

**Severity:** P1 (complete service outage if all connections consumed)
**Service:** DebtFlow PostgreSQL Database
**Last updated:** 2026-02-11

---

## Overview

DebtFlow uses PostgreSQL as its primary datastore, accessed by multiple consumers:

- **Gunicorn workers** serving the Django REST API (accounts, payments, analytics endpoints)
- **Celery workers** running background tasks (`process_payment`, `sftp_poll_all_agencies`, `process_import_file`, `reconcile_payments`, report generation, maintenance)
- **Celery Beat** scheduler
- **Django management commands** (migrations, ad-hoc scripts)

The database engine is `django_prometheus.db.backends.postgresql` (configured in `config/settings/base.py`) with a `connect_timeout` of 5 seconds. When the total number of connections across all consumers reaches PostgreSQL's `max_connections` limit, new connection attempts fail with:

```
OperationalError: FATAL: too many connections for role "debtflow"
```

or

```
OperationalError: could not connect to server: Connection refused
```

If PgBouncer is deployed in front of PostgreSQL, exhaustion can also occur at the PgBouncer layer with different symptoms.

---

## Symptoms

- Application logs show `django.db.utils.OperationalError: FATAL: too many connections`
- API returns HTTP 500 errors across all endpoints simultaneously
- Celery tasks fail with `OperationalError` and are retried (visible in Celery Flower or logs)
- Sentry floods with identical `OperationalError` exceptions
- Health check endpoint (`/health/`) fails
- PgBouncer logs: `WARNING: client_login_timeout`, `ERROR: no more connections allowed`
- Prometheus metric `django_db_errors_total` spikes
- Grafana alert: PostgreSQL connection count approaching `max_connections`

---

## Investigation Steps

### Step 1: Confirm Connection Exhaustion

**Check current connection count versus the limit:**

```sql
-- Current total connections
SELECT count(*) AS total_connections FROM pg_stat_activity;

-- Max allowed connections
SHOW max_connections;

-- Connections reserved for superuser
SHOW superuser_reserved_connections;

-- Effective limit for application role
-- Available = max_connections - superuser_reserved_connections
SELECT
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'superuser_reserved_connections') AS reserved,
    (SELECT count(*) FROM pg_stat_activity) AS current_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections')
        - (SELECT setting::int FROM pg_settings WHERE name = 'superuser_reserved_connections')
        - (SELECT count(*) FROM pg_stat_activity) AS available;
```

> **Note:** If you cannot connect as the application user, use the `postgres` superuser which has reserved connections.

### Step 2: Identify Who Is Holding Connections

```sql
-- Connections grouped by application name
SELECT
    application_name,
    state,
    count(*) AS count
FROM pg_stat_activity
WHERE datname = 'debtflow'
GROUP BY application_name, state
ORDER BY count DESC;
```

Expected application names:
- Empty or `''` = Django/Gunicorn (unless `APPLICATION_NAME` is set in `OPTIONS`)
- `celery` = Celery workers
- `pgbouncer` = PgBouncer server connections

```sql
-- Connections grouped by client address (useful for identifying which server)
SELECT
    client_addr,
    application_name,
    state,
    count(*) AS count
FROM pg_stat_activity
WHERE datname = 'debtflow'
GROUP BY client_addr, application_name, state
ORDER BY count DESC;
```

### Step 3: Find Idle and Long-Running Connections

```sql
-- Connections idle for more than 5 minutes (likely leaked)
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    now() - state_change AS idle_duration,
    now() - backend_start AS connection_age,
    left(query, 100) AS last_query
FROM pg_stat_activity
WHERE datname = 'debtflow'
  AND state = 'idle'
  AND now() - state_change > interval '5 minutes'
ORDER BY idle_duration DESC;
```

```sql
-- Long-running active queries (may be holding connections + locks)
SELECT
    pid,
    usename,
    application_name,
    state,
    now() - query_start AS query_duration,
    wait_event_type,
    wait_event,
    left(query, 150) AS query
FROM pg_stat_activity
WHERE datname = 'debtflow'
  AND state = 'active'
  AND now() - query_start > interval '30 seconds'
ORDER BY query_duration DESC;
```

### Step 4: Check for Long-Running Transactions

Long-running transactions hold connections open and can prevent connection reuse.

```sql
-- Transactions open for more than 1 minute
SELECT
    pid,
    usename,
    application_name,
    state,
    now() - xact_start AS transaction_duration,
    now() - query_start AS query_duration,
    left(query, 150) AS query
FROM pg_stat_activity
WHERE datname = 'debtflow'
  AND xact_start IS NOT NULL
  AND now() - xact_start > interval '1 minute'
ORDER BY transaction_duration DESC;
```

Common sources of long-running transactions in DebtFlow:
- `PaymentService.create_payment()` uses `@transaction.atomic` with external Stripe API calls inside the transaction (see `apps/payments/services.py` lines 120-172)
- `BatchImporter._process_batch()` runs `transaction.atomic()` per record (see `apps/integrations/importers.py` lines 71-90)
- `reconcile_payments()` task iterating over up to 100 stale payments (see `tasks/payment_tasks.py` lines 39-66)

### Step 5: Check Django CONN_MAX_AGE Configuration

```bash
# Check the current CONN_MAX_AGE setting
# In Django shell:
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default'].get('CONN_MAX_AGE', 0))"
```

**Impact of CONN_MAX_AGE:**
- `CONN_MAX_AGE = 0` (default in DebtFlow): Each request opens and closes a connection. High overhead but no leaking.
- `CONN_MAX_AGE = 600`: Connections are reused for 10 minutes. Reduces overhead but if workers leak, connections accumulate.
- `CONN_MAX_AGE = None`: Connections are kept open forever. Dangerous without PgBouncer.

> **Important:** If PgBouncer is used in `transaction` pooling mode, `CONN_MAX_AGE` **must** be `0`. Django persistent connections and PgBouncer transaction mode are incompatible because Django's connection reuse assumes session-level state.

### Step 6: Check PgBouncer Status (If Deployed)

```bash
# Connect to PgBouncer admin interface
psql -h localhost -p 6432 -U pgbouncer pgbouncer
```

```sql
-- Show pool status
SHOW POOLS;
-- Key columns: cl_active, cl_waiting, sv_active, sv_idle, sv_used, maxwait

-- Show individual client connections
SHOW CLIENTS;

-- Show server (PostgreSQL) connections managed by PgBouncer
SHOW SERVERS;

-- Show PgBouncer config
SHOW CONFIG;
-- Key settings: default_pool_size, max_client_conn, max_db_connections, reserve_pool_size

-- Show aggregate stats
SHOW STATS;
```

**What to look for:**
- `cl_waiting > 0` means clients are queued waiting for a connection
- `maxwait > 1` means significant wait times
- `sv_active` approaching `default_pool_size` means pool is saturated

### Step 7: Check Celery Worker Connection Usage

```bash
# Check how many Celery workers are running
celery -A config.celery inspect active_queues

# Check active tasks (each may hold a DB connection)
celery -A config.celery inspect active

# Check worker concurrency setting
celery -A config.celery inspect stats | grep concurrency
```

Each Celery worker process (prefork) opens its own database connection. With `CELERY_WORKER_PREFETCH_MULTIPLIER = 1` (configured in `config/settings/base.py`), workers take one task at a time, but the connection may persist between tasks.

---

## Resolution

### Immediate: Terminate Leaked/Idle Connections

```sql
-- Terminate all idle connections older than 10 minutes for the debtflow user
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'debtflow'
  AND usename = 'debtflow'
  AND state = 'idle'
  AND now() - state_change > interval '10 minutes';
```

```sql
-- Terminate specific long-running transactions that are blocking
SELECT pg_terminate_backend(<pid>);
```

> **Caution:** Terminating a connection mid-transaction causes a rollback. For `PaymentService.create_payment()`, this means the payment will be marked as FAILED and the Stripe charge may need manual reconciliation.

### Immediate: Restart Application Servers to Release Connections

```bash
# Graceful restart of Gunicorn (finishes in-flight requests, then restarts workers)
kill -HUP $(cat /var/run/gunicorn/debtflow.pid)

# Restart Celery workers (gracefully finish current tasks)
celery -A config.celery control shutdown
# Then let the process manager (systemd/supervisor) restart them
```

### Fix: Configure Connection Lifetime in Django

In `config/settings/base.py`, add `CONN_MAX_AGE` to prevent connections from living forever:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "NAME": config("DATABASE_NAME", default="debtflow"),
        "USER": config("DATABASE_USER", default="debtflow"),
        "PASSWORD": config("DATABASE_PASSWORD", default="debtflow"),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", default="5432"),
        "OPTIONS": {
            "connect_timeout": 5,
        },
        "CONN_MAX_AGE": 600,  # Close connections after 10 minutes of reuse
    }
}
```

### Fix: Configure PgBouncer Appropriately

Recommended PgBouncer settings for DebtFlow:

```ini
[databases]
debtflow = host=127.0.0.1 port=5432 dbname=debtflow

[pgbouncer]
pool_mode = transaction
default_pool_size = 25
max_client_conn = 200
max_db_connections = 80
reserve_pool_size = 5
reserve_pool_timeout = 3
server_idle_timeout = 300
client_idle_timeout = 600
log_connections = 1
log_disconnections = 1
```

Sizing rationale:
- `max_db_connections = 80` should be less than PostgreSQL's `max_connections` (typically 100) minus `superuser_reserved_connections` (typically 3)
- `max_client_conn = 200` allows Gunicorn workers + Celery workers + headroom
- `default_pool_size = 25` is per-database pool; adjust based on workload

### Fix: Increase PostgreSQL max_connections (If Needed)

```bash
# In postgresql.conf (requires restart)
max_connections = 200

# Reload or restart PostgreSQL
sudo systemctl restart postgresql
```

> **Warning:** Simply increasing `max_connections` without sufficient RAM (each connection uses ~10MB) can cause OOM issues. Prefer connection pooling via PgBouncer.

### Fix: Reduce Connection Usage by Celery Workers

```python
# In config/settings/base.py or production.py
# Close DB connections after each Celery task
from celery.signals import task_postrun

@task_postrun.connect
def close_db_connections(**kwargs):
    from django import db
    db.connections.close_all()
```

Or configure in `config/celery.py`:

```python
from celery.signals import task_postrun

@task_postrun.connect
def close_db_connection(sender=None, **kwargs):
    from django import db
    db.connections.close_all()
```

### Fix: Set PostgreSQL Statement Timeout

Prevent any single query from running indefinitely:

```sql
-- Set a default statement timeout for the debtflow role
ALTER ROLE debtflow SET statement_timeout = '30s';

-- Or set it at the database level
ALTER DATABASE debtflow SET statement_timeout = '30s';
```

The Celery `CELERY_TASK_TIME_LIMIT = 600` (configured in `config/settings/base.py`) kills the worker process after 10 minutes, but the database connection may linger as idle.

---

## Prevention

1. **Connection monitoring:** Add Grafana alerts for:
   - `pg_stat_activity` connection count > 80% of `max_connections`
   - Any `cl_waiting > 0` in PgBouncer pools
   - Connection count by `application_name` to identify unexpected growth

2. **PgBouncer in production:** Always deploy PgBouncer between Django/Celery and PostgreSQL. Use `transaction` pool mode with `CONN_MAX_AGE = 0` in Django.

3. **Celery worker sizing:** Calculate total possible connections:
   ```
   Total = (gunicorn_workers * threads) + (celery_workers * concurrency) + (celery_beat) + (management_overhead)
   ```
   Ensure this total is well below `max_connections` (or PgBouncer `max_db_connections`).

4. **Connection leak detection:** Set PostgreSQL `idle_in_transaction_session_timeout`:
   ```sql
   ALTER DATABASE debtflow SET idle_in_transaction_session_timeout = '5min';
   ```
   This automatically terminates connections that have been idle in a transaction for more than 5 minutes.

5. **Transaction scope review:** Audit code that runs external API calls inside `transaction.atomic()`. The `PaymentService.create_payment()` method (in `apps/payments/services.py`) calls Stripe inside an atomic block, which holds the connection open for the duration of the API call. Consider restructuring to:
   - Create the payment record in one transaction
   - Call Stripe outside the transaction
   - Update the payment status in a second transaction

6. **Celery connection cleanup:** Use the `task_postrun` signal to close database connections after each task completes, preventing connection accumulation across long-running worker processes.

7. **Load testing:** Simulate peak connection load (e.g., bulk SFTP import + high API traffic + payment processing) in staging to validate connection pool sizing before production deployments.

8. **PostgreSQL connection logging:** Enable `log_connections` and `log_disconnections` in `postgresql.conf` to track connection lifecycle and identify patterns of connection churn or leakage.
