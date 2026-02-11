# DebtFlow API Guide

## Base URL

```
http://localhost:8000/api/v1/
```

## Authentication

DebtFlow uses JWT (JSON Web Tokens) for authentication.

### Obtain Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

### Use Token

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/accounts/
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

## Endpoints

### Accounts

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/accounts/` | Auth | List with filters and cursor pagination |
| POST | `/accounts/` | Admin | Create new account |
| GET | `/accounts/{id}/` | Auth | Detail with debtor and activities |
| PATCH | `/accounts/{id}/` | Admin/Collector | Update allowed fields |
| POST | `/accounts/{id}/assign/` | Admin | Assign to collector |
| POST | `/accounts/{id}/add-note/` | Auth | Add note to timeline |
| GET | `/accounts/{id}/timeline/` | Auth | Activity timeline |
| POST | `/accounts/{id}/transition/` | Auth | Status transition |
| GET | `/accounts/export/` | Admin | Async CSV export |

### Payments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/payments/` | Auth | Create payment |
| GET | `/payments/` | Auth | List payments |
| GET | `/payments/{id}/` | Auth | Payment detail |
| POST | `/payments/{id}/refund/` | Admin | Initiate refund |
| POST | `/payments/webhook/stripe/` | Public (HMAC) | Stripe webhook |

### SFTP Imports

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/imports/` | Admin | List import jobs |
| GET | `/imports/{id}/` | Admin | Job detail |
| POST | `/imports/trigger/` | Admin | Manual import trigger |
| GET | `/imports/{id}/errors/` | Admin | Paginated errors |

### Analytics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/analytics/dashboard/` | Admin | KPIs |
| GET | `/analytics/collectors/` | Admin | Collector performance |
| GET | `/analytics/payments/trends/` | Admin | Payment trends |
| GET | `/analytics/aging-report/` | Admin | Aging buckets |

## Filtering & Pagination

### Filters (Accounts)

```
GET /accounts/?status=new&min_balance=1000&created_after=2024-01-01
```

### Cursor Pagination

```
GET /accounts/?cursor=cD0yMDI0LTAxLTE1
```

Response includes `next` and `previous` cursor URLs.

## Error Responses

```json
{
  "detail": "Error message here"
}
```

| Status | Meaning |
|---|---|
| 400 | Bad request / validation error |
| 401 | Not authenticated |
| 403 | Permission denied |
| 404 | Not found |
| 429 | Rate limited |
| 503 | Service unavailable (circuit breaker open) |
