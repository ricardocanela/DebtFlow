# Runbook: SFTP Import Failure

**Severity:** P3 (P2 if imports are blocked for >1 hour across multiple agencies)
**Service:** DebtFlow Celery Workers (SFTP polling + CSV import tasks)
**Last updated:** 2026-02-11

---

## Overview

DebtFlow ingests debt portfolio data from creditor clients via SFTP polling. Celery Beat schedules `sftp_poll_all_agencies` every 15 minutes, which connects to each agency's configured SFTP server, downloads new CSV files, and dispatches `process_import_file` tasks for async processing. Each file is parsed with Pydantic validation, processed in batches of 1000 records, and results are tracked via `SFTPImportJob` records.

Key components:
- **Celery Beat** — schedules the polling task
- **`sftp_poll_all_agencies`** — connects to SFTP servers, downloads files (3 retries, 60s delay)
- **`process_import_file`** — parses CSV, upserts Debtor/Account records (2 retries, 120s delay)
- **`SFTPImportJob`** model — tracks status, counts, and error details

---

## Symptoms

- `SFTPImportJob` records stuck in `processing` status for extended periods
- New `SFTPImportJob` records not being created (polling not running)
- `SFTPImportJob` records with status `failed` or high `processed_errors` count
- Prometheus alert `SFTPImportFailed` firing
- Celery worker logs showing `paramiko.ssh_exception.SSHException` or `socket.timeout`
- Creditor data not appearing in the accounts list despite files being uploaded
- Import API endpoint (`GET /api/v1/imports/`) showing stale data

---

## Investigation Steps

### Step 1: Check Recent Import Jobs

```bash
# Via API
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/imports/?ordering=-created_at

# Via Django shell
python manage.py shell -c "
from apps.integrations.models import SFTPImportJob
for job in SFTPImportJob.objects.order_by('-created_at')[:10]:
    print(f'{job.id} | {job.agency.name} | {job.status} | ok={job.processed_ok} err={job.processed_errors} | {job.created_at}')
"
```

### Step 2: Check Celery Beat Is Running

```bash
# Check if beat process is alive
ps aux | grep celery | grep beat

# Check Celery Beat logs for the scheduled task
journalctl -u debtflow-beat --since "1 hour ago" | grep sftp_poll

# In Docker
docker compose logs beat --since 1h | grep sftp_poll

# Verify the task is registered in the schedule
python manage.py shell -c "
from config.celery import app
print(app.conf.beat_schedule)
"
```

### Step 3: Check Celery Worker Health

```bash
# Check active/reserved/scheduled tasks
celery -A config inspect active
celery -A config inspect reserved
celery -A config inspect scheduled

# Check for failed tasks in the last hour
celery -A config inspect stats

# Check worker logs for errors
journalctl -u debtflow-worker --since "1 hour ago" | grep -i "error\|exception\|fail"

# In Docker
docker compose logs worker --since 1h | grep -iE "error|exception|fail|sftp"
```

### Step 4: Test SFTP Connectivity

```bash
# Test connection to agency's SFTP server manually
python manage.py shell -c "
from apps.accounts.models import Agency
from apps.integrations.sftp_client import SFTPClient

for agency in Agency.objects.filter(is_active=True):
    settings = agency.settings or {}
    sftp_config = settings.get('sftp', {})
    if not sftp_config.get('enabled'):
        continue
    print(f'Testing {agency.name}...')
    try:
        client = SFTPClient(
            host=sftp_config['host'],
            port=sftp_config.get('port', 22),
            username=sftp_config['username'],
            password=sftp_config.get('password', ''),
        )
        with client:
            files = client.list_files(sftp_config.get('remote_dir', '/upload'))
            print(f'  Connected OK. Files found: {len(files)}')
            for f in files[:5]:
                print(f'    - {f}')
    except Exception as e:
        print(f'  FAILED: {e}')
"
```

### Step 5: Check Import Job Errors

```bash
# Get error details for a specific failed job
python manage.py shell -c "
from apps.integrations.models import SFTPImportJob
job = SFTPImportJob.objects.filter(status='failed').order_by('-created_at').first()
if job:
    print(f'Job: {job.id}')
    print(f'File: {job.file_name}')
    print(f'Status: {job.status}')
    print(f'Total: {job.total_records}, OK: {job.processed_ok}, Errors: {job.processed_errors}')
    for err in (job.error_details or [])[:20]:
        print(f'  Line {err.get(\"line\")}: {err.get(\"errors\")}')
"

# Via API
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/imports/<job-id>/errors/
```

### Step 6: Check Database State

```sql
-- Check for stuck import jobs
SELECT id, agency_id, status, file_name, total_records,
       processed_ok, processed_errors, created_at, updated_at
FROM integrations_sftpimportjob
WHERE status = 'processing'
AND updated_at < NOW() - INTERVAL '30 minutes'
ORDER BY created_at DESC;

-- Check recent account creation rate (should correlate with imports)
SELECT DATE_TRUNC('hour', created_at) AS hour,
       COUNT(*) AS accounts_created
FROM accounts_account
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1 DESC;

-- Check for duplicate external_refs that might cause conflicts
SELECT external_ref, COUNT(*)
FROM accounts_account
GROUP BY external_ref
HAVING COUNT(*) > 1;
```

---

## Resolution Steps

### Scenario 1: SFTP Server Unreachable

**Cause:** Network issues, DNS failure, firewall changes, or SFTP server down.

```bash
# Test basic connectivity
nc -zv <sftp_host> <sftp_port>

# Check DNS resolution
nslookup <sftp_host>

# Check if the issue is with our network or the remote server
traceroute <sftp_host>
```

**Resolution:**
1. If the remote SFTP server is down, contact the creditor client
2. If it's a network/firewall issue, check VPC security groups and NACLs
3. The polling task will automatically retry (3 attempts with 60s delay)
4. Once connectivity is restored, imports will resume on the next poll cycle

### Scenario 2: Authentication Failure

**Cause:** Expired credentials, changed password, or SSH key rotation.

```bash
# Check for auth errors in logs
docker compose logs worker --since 4h | grep -i "auth\|permission\|denied"
```

**Resolution:**
1. Verify credentials with the creditor client
2. Update agency SFTP settings via Django admin or API
3. Test connectivity (Step 4 above)
4. Trigger a manual poll to verify

### Scenario 3: Malformed CSV Data

**Cause:** Creditor sent a file with invalid format, missing required columns, or bad data.

**Resolution:**
1. Check error details on the `SFTPImportJob` (Step 5 above)
2. Common issues:
   - Missing required columns (`external_ref`, `debtor_name`, `original_amount`)
   - Invalid `original_amount` (negative or non-numeric)
   - Invalid `debtor_ssn_last4` (not exactly 4 digits)
   - Invalid `due_date` (not YYYY-MM-DD format)
   - Invalid email format
3. Per-row errors don't block the entire batch — valid rows are still imported
4. If the entire file is invalid (wrong headers), contact the creditor to fix the format

### Scenario 4: Stuck Processing Jobs

**Cause:** Worker crashed mid-import, task was killed, or database deadlock.

```bash
# Find stuck jobs
python manage.py shell -c "
from apps.integrations.models import SFTPImportJob
from django.utils import timezone
from datetime import timedelta

stuck = SFTPImportJob.objects.filter(
    status='processing',
    updated_at__lt=timezone.now() - timedelta(minutes=30)
)
for job in stuck:
    print(f'{job.id} | {job.file_name} | started {job.created_at}')
"
```

**Resolution:**
1. Mark stuck jobs as failed so they can be re-processed:
```bash
python manage.py shell -c "
from apps.integrations.models import SFTPImportJob
from django.utils import timezone
from datetime import timedelta

updated = SFTPImportJob.objects.filter(
    status='processing',
    updated_at__lt=timezone.now() - timedelta(minutes=30)
).update(status='failed')
print(f'Marked {updated} stuck jobs as failed')
"
```
2. Check worker health and restart if needed
3. The next polling cycle will re-download and re-process (idempotent via `update_or_create`)

### Scenario 5: Disk Space / Temp File Issues

**Cause:** Temp directory full, files not being cleaned up after import.

```bash
# Check temp directory usage
df -h /tmp
ls -la /tmp/sftp_import_*

# Clean up orphaned temp files (older than 1 day)
find /tmp -name "sftp_import_*" -mtime +1 -delete
```

---

## Manual Import Trigger

If automatic polling has been disrupted, you can manually trigger a poll:

```bash
# Trigger via Celery
python manage.py shell -c "
from tasks.sftp_tasks import sftp_poll_all_agencies
result = sftp_poll_all_agencies.delay()
print(f'Task dispatched: {result.id}')
"

# Or trigger for a specific agency via the API
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/imports/trigger/
```

---

## Prevention

1. **Monitoring:** Ensure Prometheus alert `SFTPImportFailed` is active and routed to the on-call channel
2. **Credentials rotation:** Establish a process with creditor clients for credential rotation with advance notice
3. **CSV validation docs:** Share the expected CSV format with creditor clients (see README Data Ingestion section)
4. **Health checks:** The Celery Beat schedule ensures polling runs every 15 minutes — monitor Beat process health
5. **Temp file cleanup:** The `process_import_file` task cleans up temp files in a `finally` block; periodic cleanup cron as backup

---

## Escalation

| Level | Condition | Action |
|-------|-----------|--------|
| L1 | Single agency import failed | Check connectivity and error details |
| L2 | Multiple agencies failing or stuck >1 hour | Investigate worker health, restart services |
| L3 | Data corruption or duplicate records | Engage senior engineer, check database integrity |
