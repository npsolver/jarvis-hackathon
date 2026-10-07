# Banking transaction system

Implements `Design.md`: Account / Transaction / HumanReview tables in
PostgreSQL, a Django + DRF API layer, and the review -> migrate -> human
review loop described in the design doc.

## Layout

- `banking/models.py` -- 1.1/1.2/1.3: `Account`, `Transaction`, `HumanReview`.
- `banking/views.py` + `banking/urls.py` -- 2.1 user APIs (create account,
  make a transaction, list/inspect reviews).
- `banking/services/review.py` -- 2.2 data review script. Shared by the user
  APIs and the CSV importer; validates a raw record and returns pass/fail
  with reasons.
- `banking/services/migration.py` -- 2.3 data migration script. Writes a
  validated record into the tables and applies the account balance effects.
- `banking/services/review_queue.py` -- 2.4 send-to-review API. Parks a
  failed record (with reasons) in `HumanReview`.
- `banking/services/resolution.py` -- 2.5 add/remove API. `remove_review`
  rejects a record outright; `add_review` re-runs the review script (with
  any admin corrections merged in) and either migrates it or sends it back
  to the review table with updated reasons.
- `banking/management/commands/import_csv.py` -- CSV migration script.
  Streams `accounts (1).csv` / `transactions (1).csv` through the same
  intake path as the API.
- `banking/models.py` `Profile` + `banking/auth_views.py` + `banking/permissions.py` --
  login/roles. A `Profile` links a Django `User` to a role (`USER`/`ADMIN`)
  and, for a `USER`, the one `Account` they're allowed to act as.
  `banking/management/commands/seed_users.py` creates a demo admin login
  plus one login per `Account` (username = `accountId`).

## Setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # adjust POSTGRES_* if needed
```

Start Postgres (skip if you already have one running -- this repo's dev
Postgres container is `jarvis-hackathon-db-1`, db/user/password `banking`,
matching `.env.example`):

```bash
docker run -d --name jarvis-hackathon-db \
  -e POSTGRES_DB=banking -e POSTGRES_USER=banking -e POSTGRES_PASSWORD=banking \
  -p 5432:5432 postgres:16
```

Apply migrations:

```bash
python manage.py migrate
```

## Migrate the CSVs

```bash
python manage.py import_csv
# or: python manage.py import_csv --accounts path/to/accounts.csv --transactions path/to/transactions.csv
```

Prints a summary (migrated vs. sent to review) and, for anything flagged,
the review id and reason.

## Logins

```bash
python manage.py seed_users
# admin login: admin / admin123
# one login per account, username = accountId (e.g. ACC1001), password = password123
```

Re-running `seed_users` is safe -- it upserts, so run it again after
re-importing the CSVs.

## Run the API

```bash
python manage.py runserver   # http://localhost:8000
```

All endpoints below (except login) require `Authorization: Token <token>`.

- `POST /api/auth/login/` -- body `{"username", "password"}` -> `{token, username, role, account_id}`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`
- `GET/POST /api/accounts/`, `GET /api/accounts/<account_id>/` -- an admin
  sees/creates any account; a `USER` only ever sees their own linked account
  (account creation is admin-only).
- `GET/POST /api/transactions/`, `GET /api/transactions/<transaction_id>/` --
  an admin sees everything; a `USER` only sees transactions touching their
  own account, and can only move money out of their own account
  (`fromAccount` must match their `account_id` or be omitted).
- `GET /api/reviews/` (optional `?status=PENDING|APPROVED|REJECTED`), `GET /api/reviews/<id>/` -- admin only.
- `POST /api/reviews/<id>/add/` -- admin only. Body `{"overrides": {...}, "resolved_by": "..."}`
- `POST /api/reviews/<id>/remove/` -- admin only. Body `{"resolved_by": "..."}`

POST bodies for accounts/transactions use the CSV column names
(`accountId`, `customerName`, ..., `transactionId`, `fromAccount`,
`toAccount`, ...) -- the same shape as a CSV row, since both paths share the
review script.

A plain Django admin is also wired up at `/admin/` (log in with the seeded
`admin` user) for browsing all four tables directly.

## CORS

`corsheaders` is configured to allow the Vite dev server
(`http://localhost:5173`) by default; override with `CORS_ALLOWED_ORIGINS`
(comma-separated) in `.env` if the frontend runs elsewhere.
