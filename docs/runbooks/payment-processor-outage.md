# Runbook: Payment Processor Outage

**Severity:** P1 (direct revenue impact — payments cannot be processed)
**Service:** DebtFlow Payments (Stripe integration via Celery workers)
**Last updated:** 2026-02-11

---

## Overview

DebtFlow processes debt payments through Stripe via the `PaymentService`. The integration includes:

- **Circuit Breaker** — Redis-backed (5 failures in 60s opens the circuit, half-open after 30s)
- **Idempotency** — Redis-backed keys (24h TTL) prevent duplicate charges
- **Webhooks** — Stripe sends `payment_intent.succeeded`, `payment_intent.failed`, `charge.refunded`, `charge.dispute.created` events with HMAC-SHA256 verification
- **Retry Logic** — `process_payment` Celery task retries 3 times with exponential backoff (2s, 4s, 8s)

When Stripe is down or degraded, the circuit breaker opens to protect both systems, and payments fail fast with `ServiceUnavailableError`.

---

## Symptoms

- Prometheus alert `PaymentProcessorDown` firing (circuit breaker in open state)
- Payment creation API returning `503 Service Unavailable` responses
- `Payment` records stuck in `pending` status
- Users/collectors unable to record payments
- Celery worker logs showing `stripe.error.APIConnectionError` or `ServiceUnavailableError`
- Webhook endpoint receiving fewer events than expected
- Circuit breaker state in Redis showing `open`

---

## Investigation Steps

### Step 1: Check Stripe Status

```bash
# Check Stripe's official status page
curl -s https://status.stripe.com/api/v2/status.json | python -m json.tool

# Or visit: https://status.stripe.com
```

### Step 2: Check Circuit Breaker State

```bash
# Check circuit breaker state in Redis
python manage.py shell -c "
import redis
from django.conf import settings

r = redis.from_url(settings.REDIS_URL)
state = r.get('circuit_breaker:stripe:state')
failures = r.get('circuit_breaker:stripe:failures')
last_failure = r.get('circuit_breaker:stripe:last_failure')
print(f'State: {state}')
print(f'Failures: {failures}')
print(f'Last failure time: {last_failure}')
"

# Check directly via redis-cli
redis-cli -h <redis_host> GET circuit_breaker:stripe:state
redis-cli -h <redis_host> GET circuit_breaker:stripe:failures
```

### Step 3: Check Recent Payment Failures

```bash
# Check failed payments in the database
python manage.py shell -c "
from apps.payments.models import Payment
from django.utils import timezone
from datetime import timedelta

recent = Payment.objects.filter(
    created_at__gte=timezone.now() - timedelta(hours=1)
).values('status').annotate(
    count=__import__('django.db.models', fromlist=['Count']).Count('id')
)
for r in recent:
    print(f'{r[\"status\"]}: {r[\"count\"]}')

# Show recent failures
failures = Payment.objects.filter(
    status='failed',
    created_at__gte=timezone.now() - timedelta(hours=1)
).order_by('-created_at')[:10]
for p in failures:
    print(f'{p.id} | {p.amount} | {p.created_at} | {p.metadata}')
"
```

```sql
-- Check payment failure rate over the last 24 hours
SELECT DATE_TRUNC('hour', created_at) AS hour,
       status,
       COUNT(*) AS count
FROM payments_payment
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- Check pending payments that may need reconciliation
SELECT id, account_id, amount, idempotency_key, created_at
FROM payments_payment
WHERE status = 'pending'
AND created_at < NOW() - INTERVAL '30 minutes'
ORDER BY created_at DESC;
```

### Step 4: Check Celery Worker Logs

```bash
# Check for Stripe-related errors in worker logs
journalctl -u debtflow-worker --since "1 hour ago" | grep -iE "stripe|payment|circuit"

# In Docker
docker compose logs worker --since 1h | grep -iE "stripe|payment|circuit|503"

# Check active payment tasks
celery -A config inspect active | grep process_payment
celery -A config inspect reserved | grep process_payment
```

### Step 5: Check Webhook Delivery

```bash
# Check recent webhook events processed
python manage.py shell -c "
from apps.audit.models import AuditLog
logs = AuditLog.objects.filter(
    action='webhook_received'
).order_by('-timestamp')[:10]
for log in logs:
    print(f'{log.timestamp} | {log.changes}')
"

# Check if webhook endpoint is responding
curl -s -o /dev/null -w '%{http_code}' \
  -X POST http://localhost:8000/api/v1/payments/webhook/stripe/ \
  -H "Content-Type: application/json" \
  -d '{}'
# Should return 400 (invalid signature), NOT 500
```

### Step 6: Check Stripe API Connectivity

```bash
# Test direct Stripe API connectivity
python manage.py shell -c "
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    stripe.Account.retrieve()
    print('Stripe API: CONNECTED')
except stripe.error.AuthenticationError:
    print('Stripe API: AUTH ERROR (check API key)')
except stripe.error.APIConnectionError as e:
    print(f'Stripe API: CONNECTION ERROR ({e})')
except Exception as e:
    print(f'Stripe API: ERROR ({e})')
"
```

---

## Resolution Steps

### Scenario 1: Stripe Is Down (Global Outage)

**Cause:** Stripe is experiencing a service disruption.

**Resolution:**
1. Confirm via [status.stripe.com](https://status.stripe.com)
2. The circuit breaker will automatically open, preventing cascading failures
3. **Do NOT manually retry payments** — wait for Stripe to recover
4. Communicate to users that payment processing is temporarily unavailable
5. The circuit breaker will automatically transition to half-open after 30 seconds and test with a single request
6. Once Stripe recovers, the circuit will close and payments will resume
7. Run payment reconciliation to catch up on any missed updates:

```bash
python manage.py shell -c "
from tasks.payment_tasks import reconcile_payments
result = reconcile_payments.delay()
print(f'Reconciliation task dispatched: {result.id}')
"
```

### Scenario 2: Circuit Breaker Stuck Open

**Cause:** Stripe recovered but circuit breaker hasn't transitioned to half-open, or the half-open test keeps failing.

```bash
# Check the recovery timeout
python manage.py shell -c "
import redis, time
from django.conf import settings

r = redis.from_url(settings.REDIS_URL)
last_failure = r.get('circuit_breaker:stripe:last_failure')
if last_failure:
    elapsed = time.time() - float(last_failure)
    print(f'Seconds since last failure: {elapsed:.0f}')
    print(f'Recovery timeout: 30s')
    print(f'Should be half-open: {elapsed > 30}')
"
```

**Resolution:**
1. Verify Stripe is actually healthy (Step 6 above)
2. If Stripe is healthy, manually reset the circuit breaker:

```bash
python manage.py shell -c "
import redis
from django.conf import settings

r = redis.from_url(settings.REDIS_URL)
r.delete('circuit_breaker:stripe:state')
r.delete('circuit_breaker:stripe:failures')
r.delete('circuit_breaker:stripe:last_failure')
print('Circuit breaker reset to closed state')
"
```

3. Monitor the next few payments to ensure they succeed

### Scenario 3: Authentication / API Key Issues

**Cause:** Stripe API key expired, rotated, or misconfigured.

**Resolution:**
1. Verify the API key in the environment:
```bash
# Check if the key is set (don't print the full key)
python manage.py shell -c "
from django.conf import settings
key = settings.STRIPE_SECRET_KEY
print(f'Key set: {bool(key)}')
print(f'Key prefix: {key[:7]}...' if key else 'NOT SET')
print(f'Starts with sk_test: {key.startswith(\"sk_test\")}' if key else '')
print(f'Starts with sk_live: {key.startswith(\"sk_live\")}' if key else '')
"
```
2. If the key is wrong, update it in the environment/secrets:
   - **Kubernetes:** Update the `debtflow-secret` and restart pods
   - **Docker:** Update `.env` and `docker compose up -d`
3. Also verify the webhook secret is correct if webhooks are failing

### Scenario 4: Pending Payments Needing Reconciliation

**Cause:** Payments were sent to Stripe but the response was lost (network issue, worker crash), leaving them in `pending` status.

**Resolution:**
1. Run the reconciliation task:
```bash
python manage.py shell -c "
from tasks.payment_tasks import reconcile_payments
result = reconcile_payments.delay()
print(f'Task dispatched: {result.id}')
"
```
2. The task checks each stale pending payment against Stripe's API and updates status accordingly
3. If automatic reconciliation fails, manually check specific payments:

```bash
python manage.py shell -c "
import stripe
from django.conf import settings
from apps.payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

pending = Payment.objects.filter(
    status='pending',
    processor_ref__isnull=False
).order_by('created_at')[:20]

for payment in pending:
    try:
        pi = stripe.PaymentIntent.retrieve(payment.processor_ref)
        print(f'{payment.id} | Stripe status: {pi.status} | Our status: {payment.status}')
    except Exception as e:
        print(f'{payment.id} | Error: {e}')
"
```

### Scenario 5: Webhook Delivery Issues

**Cause:** Stripe can't reach our webhook endpoint, or HMAC validation is failing.

```bash
# Check if the webhook endpoint is accessible externally
# (from outside the cluster/container)
curl -I https://debtflow.example.com/api/v1/payments/webhook/stripe/

# Check webhook secret matches
python manage.py shell -c "
from django.conf import settings
secret = settings.STRIPE_WEBHOOK_SECRET
print(f'Webhook secret set: {bool(secret)}')
print(f'Secret prefix: {secret[:8]}...' if secret else 'NOT SET')
"
```

**Resolution:**
1. If the endpoint is unreachable:
   - Check ingress/load balancer configuration
   - Ensure the webhook URL is correct in Stripe Dashboard
   - Verify no firewall rules blocking Stripe IPs
2. If HMAC validation is failing:
   - Verify the webhook signing secret in Stripe Dashboard matches `STRIPE_WEBHOOK_SECRET`
   - Stripe rotates secrets when you regenerate the webhook endpoint — update the secret
3. Check Stripe Dashboard > Webhooks for delivery failures and retry from there

---

## Idempotency Considerations

- All payment operations use idempotency keys stored in Redis (24h TTL)
- Re-processing a payment with the same idempotency key is safe — it will return the existing result
- Webhook events are deduplicated via Redis — processing the same event twice is safe
- The `reconcile_payments` task is safe to run multiple times

---

## Prevention

1. **Circuit breaker tuning:** Current settings (5 failures/60s window, 30s recovery) — adjust in `PaymentService` if needed
2. **Monitoring:** Ensure `PaymentProcessorDown` alert fires when circuit opens
3. **Stripe API key rotation:** Use the Stripe Dashboard to manage key rotation with overlap periods
4. **Webhook redundancy:** Consider adding a secondary webhook endpoint or using Stripe's event polling as fallback
5. **Payment reconciliation:** Runs daily via Celery Beat — verify it's scheduled and completing successfully
6. **Load testing:** Periodically test payment flow under load to ensure circuit breaker behaves correctly

---

## Key Metrics to Monitor

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Circuit breaker state | `open` | `PaymentProcessorDown` |
| Payment failure rate | >10% in 5min | P2 |
| Pending payments age | >30min | Reconciliation needed |
| Webhook delivery success | <95% | Check endpoint health |
| Payment p95 latency | >5s | Check Stripe API latency |

---

## Escalation

| Level | Condition | Action |
|-------|-----------|--------|
| L1 | Stripe degraded, circuit breaker handling it | Monitor, communicate ETA |
| L2 | Payments failing >30 min, reconciliation needed | Run reconciliation, check for stuck payments |
| L3 | Data inconsistency (charged but not recorded) | Senior engineer + manual Stripe Dashboard review |
| P1 | Complete payment outage >1 hour | Incident commander, Stripe support case |
