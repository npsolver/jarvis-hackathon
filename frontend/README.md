# Jarvis Banking -- frontend

React + Vite client for the Django backend in `../backend`. Logs in as
either a customer (role `USER`, scoped to their own account) or an admin
(role `ADMIN`, full access + the human review queue), based on whatever the
backend's `/api/auth/login/` returns -- there's no separate "login as"
toggle, the role comes from the account.

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # VITE_API_BASE_URL, defaults to http://localhost:8000/api
npm run dev                  # http://localhost:5173
```

Make sure the backend is running first (see `../backend/README.md`) and has
been seeded (`python manage.py import_csv && python manage.py seed_users`).

## Demo logins

- Admin: `admin` / `admin123`
- Any customer: username = an `accountId` from `accounts (1).csv` (e.g.
  `ACC1001`), password = `password123`

Both are pre-filled via the "Use demo login" buttons on the sign-in page.

## What's where

- `src/api.js` -- fetch wrapper; attaches `Authorization: Token <token>`
  from `localStorage` to every request.
- `src/App.jsx` -- holds the logged-in user (`{username, role, account_id}`)
  in `localStorage` + state, and picks `UserDashboard` or `AdminDashboard`
  based on `role`.
- `src/pages/Login.jsx` -- single login form for both roles.
- `src/pages/UserDashboard.jsx` + `src/components/TransactionForm.jsx` --
  a customer's own account/balance, their transaction history, and a form
  to submit a new transaction (goes through the backend's review script;
  shows "sent for review" if it gets flagged).
- `src/pages/AdminDashboard.jsx` + `src/components/ReviewRow.jsx` -- all
  accounts/transactions, and the human review queue with inline-editable
  fields plus Add (re-review + migrate) / Remove (reject) actions.
