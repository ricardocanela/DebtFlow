# DebtFlow — Performance Documentation

## Index Strategy

All indexes are designed for real system queries and validated with `EXPLAIN (ANALYZE, BUFFERS)`.

### Account Indexes

| Index | Type | Query It Serves |
|---|---|---|
| `(agency_id, status, created_at)` | Composite B-tree | Main listing: accounts by agency filtered by status |
| `(agency_id, assigned_to_id)` | Composite B-tree | Accounts by collector within an agency |
| `(status) WHERE status IN ('new','assigned')` | Partial index | Dashboard: pending accounts (most frequent query) |
| `(external_ref)` | B-tree unique | Deduplication during SFTP import |

### Payment Indexes

| Index | Type | Query It Serves |
|---|---|---|
| `(account_id, created_at)` | Composite B-tree | Payment history for an account |
| `(status, created_at)` | Composite B-tree | Payment reports by period |
| `(idempotency_key)` | B-tree unique | Idempotency check |

### Other Indexes

| Table | Index | Purpose |
|---|---|---|
| Debtor | `(full_name) gin_trgm_ops` | Partial name search (LIKE/ILIKE) |
| Debtor | `(external_ref)` unique | Fast lookup during SFTP import |
| AuditLog | `(content_type_id, object_id, created_at)` | Activity timeline for an object |
| SFTPImportJob | `(agency_id, status, created_at)` | Import dashboard by agency |

## Query Optimization Notes

### Account List Query
```sql
-- With composite index on (agency_id, status, created_at)
-- Index scan instead of sequential scan
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM accounts_account
WHERE agency_id = 'uuid' AND status = 'new'
ORDER BY created_at DESC
LIMIT 50;
```

### Debtor Name Search
```sql
-- With GIN trigram index on full_name
-- Enables efficient ILIKE queries
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM accounts_debtor
WHERE full_name ILIKE '%john%';
```

### Payment Aggregation
```sql
-- Uses index on (status, created_at) for range queries
EXPLAIN (ANALYZE, BUFFERS)
SELECT DATE_TRUNC('day', created_at) as day,
       SUM(amount) as total,
       COUNT(*) as count
FROM payments_payment
WHERE status = 'completed'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

## Connection Pooling

- Django `CONN_MAX_AGE`: 600s (reuse connections)
- PostgreSQL `max_connections`: 100 (default)
- Production: Use PgBouncer in front of RDS

## AuditLog Partitioning

Monthly RANGE partitioning on `created_at`:
- Enables fast queries on recent data
- Old partitions can be detached and archived to S3
- Retention: 24 months online
