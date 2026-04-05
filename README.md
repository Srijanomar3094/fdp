# Finance Backend

A Django-based backend for a finance dashboard system with role-based access control, financial record management, and summary analytics.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Django 5.1.6 |
| Database | MySQL 8 |
| Auth | Django session-based authentication |
| Access Control | Custom RBAC decorators |
| API Style | Pure Django function-based views (JSON) |

---

## Project Structure

```
zorvyn-task/
├── finance_backend/      # Django project config (settings, urls, wsgi)
├── core/                 # Shared: BaseModel + DeletedManager
├── users/                # User management, auth, RBAC decorators
│   └── management/
│       └── commands/
│           └── seed_data.py
├── finance/              # Financial records (transactions)
├── dashboard/            # Summary analytics endpoints
├── manage.py
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create MySQL database

```sql
CREATE DATABASE zor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

The database is configured in `finance_backend/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zor',
        'USER': '***',
        'PASSWORD': '***',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Seed sample data

```bash
python manage.py seed_data
```

This creates three users and 20 sample transactions:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |
| `analyst` | `analyst123` | Analyst |
| `viewer` | `viewer123` | Viewer |

To clear and re-seed:
```bash
python manage.py seed_data --clear
```

### 5. Start the server

```bash
python manage.py runserver
```

---

## Roles and Permissions

| Action | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| Login / view own profile | ✓ | ✓ | ✓ |
| View transactions | ✓ | ✓ | ✓ |
| Create / update transactions | ✗ | ✓ | ✓ |
| Delete transactions (soft) | ✗ | ✗ | ✓ |
| View dashboard summary | ✓ | ✓ | ✓ |
| View category breakdown | ✓ | ✓ | ✓ |
| View recent activity | ✓ | ✓ | ✓ |
| View monthly trends | ✗ | ✓ | ✓ |
| Manage users (CRUD) | ✗ | ✗ | ✓ |

---

## API Reference

All endpoints are JSON. Session cookie (`sessionid`) is used for authentication.

### Authentication

#### POST `/api/auth/login/`
```json
{ "username": "admin", "password": "admin123" }
```
Response: `200 OK` with user object and sets `sessionid` cookie.

#### POST `/api/auth/logout/`
Clears session. Requires auth.

#### GET `/api/auth/me/`
Returns the current authenticated user's profile.

---

### User Management _(admin only)_

#### GET `/api/users/`
List all users.

#### POST `/api/users/`
Create a new user.
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "pass123",
  "role": "analyst",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### GET `/api/users/<id>/`
Get a specific user.

#### PUT `/api/users/<id>/`
Update a user. All fields optional.
```json
{ "role": "viewer", "is_active": false }
```

#### DELETE `/api/users/<id>/`
Deactivate (soft delete) a user.

---

### Transactions

#### GET `/api/finance/transactions/`
List transactions. Supports filtering and pagination.

| Query Param | Description | Example |
|---|---|---|
| `type` | Filter by type | `?type=income` |
| `category` | Filter by category | `?category=food` |
| `start_date` | Filter from date | `?start_date=2024-01-01` |
| `end_date` | Filter until date | `?end_date=2024-12-31` |
| `search` | Search title/notes | `?search=salary` |
| `page` | Page number | `?page=2` |
| `per_page` | Results per page (max 100) | `?per_page=10` |

#### POST `/api/finance/transactions/` _(admin, analyst)_
```json
{
  "title": "Monthly Salary",
  "amount": "85000.00",
  "transaction_type": "income",
  "category": "salary",
  "date": "2024-04-01",
  "notes": "April salary"
}
```

#### GET `/api/finance/transactions/<id>/`
Get a single transaction.

#### PUT `/api/finance/transactions/<id>/` _(admin, analyst)_
Update a transaction. All fields optional.

#### DELETE `/api/finance/transactions/<id>/` _(admin only)_
Soft delete a transaction (excluded from future queries).

#### GET `/api/finance/categories/`
Returns valid categories and transaction types.

---

### Dashboard

#### GET `/api/dashboard/summary/`
```json
{
  "summary": {
    "total_income": "142700.00",
    "total_expense": "45900.00",
    "net_balance": "96800.00",
    "transaction_count": 20
  }
}
```

#### GET `/api/dashboard/categories/`
Category-wise totals. Optional `?type=income` or `?type=expense`.

#### GET `/api/dashboard/trends/` _(admin, analyst)_
Monthly income and expense totals for the past 12 months.

#### GET `/api/dashboard/recent/`
Most recent transactions. Optional `?limit=10` (max 50).

---

### Utility

#### GET `/health/`
Service health check. No auth required.

---

## Valid Categories

`salary`, `freelance`, `investment`, `rent`, `utilities`, `food`, `transport`, `healthcare`, `entertainment`, `other`

---

## Error Responses

All errors follow a consistent format:

```json
{ "error": "Description of what went wrong" }
```

Validation errors return field-level detail:
```json
{
  "errors": {
    "amount": "Amount must be a positive number",
    "date": "This field is required"
  }
}
```

| Status | Meaning |
|---|---|
| `400` | Bad request / validation error |
| `401` | Not authenticated |
| `403` | Authenticated but insufficient role |
| `404` | Resource not found |
| `405` | Method not allowed |

---

## Design Notes

### BaseModel + DeletedManager
All models (except `User`) extend `core.BaseModel`:
- `status = BooleanField(default=True)` — False means soft-deleted
- `DeletedManager` (the default `objects` manager) automatically excludes `status=False`
- `all_objects` manager bypasses the filter for admin/recovery use
- `soft_delete()` sets `status=False` and updates `updated_at`

`User` follows the same pattern using Django's built-in `is_active` field instead.

### RBAC
Implemented via two simple decorators in `users/decorators.py`:
- `@login_required_json` — returns 401 if not authenticated
- `@role_required('admin', 'analyst')` — returns 403 if role not in the allowed list

These are applied directly on view functions, keeping access control explicit and easy to audit.

### CSRF
API views use `@csrf_exempt`. This is intentional for a JSON API consumed by external clients (Postman, frontend SPA, etc.). In a production setup, CSRF protection would be enforced via `SameSite` cookie policy or CSRF headers with a trusted origin list.

### Session Auth
Django's built-in session framework is used. On login, Django creates a `sessionid` cookie. All subsequent requests must include this cookie. Sessions expire after 24 hours (`SESSION_COOKIE_AGE = 86400`).

### Assumptions
1. Amounts are stored as `DECIMAL(12,2)` — sufficient for most personal/SME finance use cases.
2. Dates are stored as `DATE` (not datetime) since financial entries typically reference a calendar date.
3. Soft-deleted transactions are excluded from all list and dashboard queries by default.
4. Admin role automatically gains Django staff/superuser access (for `/admin/` panel).
5. Viewers can see all transactions but cannot create, update, or delete them.
6. There is no concept of "per-user" data isolation — all authenticated users see all records. This matches a shared finance dashboard scenario.
