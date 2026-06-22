---
# Spec: Add Expense

## Overview

This feature enables authenticated users to record a new expense in Spendly. It replaces the placeholder `/expenses/add` route with a real form and POST handler that validates the input and inserts a row into the `expenses` table tied to the logged-in user. This is the first expense-mutating step in the roadmap and is the prerequisite for editing (step 08) and deleting (step 09) expenses. Once this step ships, the dashboard, profile, and listing pages will begin reflecting real user activity instead of only the demo seed data.

## Depends on

- 01-database-setup (the `expenses` table must exist with columns `user_id`, `amount`, `category`, `date`, `description`, `created_at`)
- 02-registration (users must exist in the `users` table)
- 03-login-logout (users must be able to log in; `session['user_id']` must be available)

## Routes

- GET /expenses/add — display the "Add expense" form — access level: logged-in
- POST /expenses/add — validate the submitted form, insert the expense into the database, redirect to `/dashboard` on success — access level: logged-in

Note: the existing placeholder route at `GET /expenses/add` will be replaced; the new route will accept both GET and POST.

## Database changes

No database changes — the `expenses` table already contains every required column (`amount`, `category`, `date`, `description`, `created_at`) and the `user_id` foreign key needed for this feature.

## Templates

- **Create:**
  - templates/add_expense.html — form with amount, category, date, and description fields, plus validation error display
- **Modify:**
  - templates/dashboard.html — ensure the "Add expense" link points to `/expenses/add` (no layout change if already wired correctly)

## Files to change

- app.py — replace the placeholder `add_expense` route with a real implementation that handles GET (render form) and POST (validate + insert). Use `session['user_id']` to scope the inserted row.

## Files to create

- templates/add_expense.html — Jinja template that extends `base.html` and renders the add-expense form

## New dependencies

No new dependencies — uses the existing Flask, sqlite3, and werkzeug stack.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only (use `?` placeholders, never f-strings in SQL)
- Passwords hashed with werkzeug (not relevant here, but maintain the convention)
- Use CSS variables — never hardcode hex values in any new or modified CSS
- All templates extend `base.html`
- Form fields and validation rules:
  - `amount` — required, must parse as a float, must be greater than 0
  - `category` — required, must be one of the allowed list (Food, Transport, Bills, Health, Entertainment, Shopping, Other); strip whitespace
  - `date` — required, must match `YYYY-MM-DD`; default to today if left blank is acceptable but the field should be present and editable
  - `description` — optional, free text; strip whitespace; cap at 255 characters
- On validation failure, re-render `add_expense.html` with the submitted values preserved (except password-like fields) and a single `error` string
- On success, commit the row, close the connection, and redirect to `/dashboard`
- Always scope the insert by `session['user_id']` so users can only add expenses to their own account
- Wrap the DB work in `try / except / finally` so the connection is closed even on errors; on exception, render `error.html` with HTTP 500
- Escape all user-supplied data in the template to prevent XSS (Jinja autoescape is sufficient)
- Do not introduce any new pip packages

## Definition of done

- [ ] GET /expenses/add when logged in renders the add-expense form
- [ ] GET /expenses/add when not logged in redirects to /login
- [ ] Submitting the form with a valid amount, category, date, and optional description creates a new row in the `expenses` table for the logged-in user
- [ ] After a successful insert the user is redirected to /dashboard
- [ ] Submitting with a missing amount shows a validation error and re-renders the form
- [ ] Submitting with a non-numeric or non-positive amount shows a validation error and re-renders the form
- [ ] Submitting with a missing or unsupported category shows a validation error and re-renders the form
- [ ] Submitting with a missing or malformed date shows a validation error and re-renders the form
- [ ] An inserted expense immediately appears on /dashboard in the recent-expenses list
- [ ] An inserted expense immediately appears on /profile (within the last-30-days default range)
- [ ] An inserted expense immediately appears on /expenses
- [ ] The `user_id` on the inserted row equals `session['user_id']` for the logged-in user
- [ ] No SQL injection vulnerabilities — all queries use parameterised `?` placeholders
- [ ] No hardcoded hex colors — any new CSS uses existing CSS variables
- [ ] Application starts without errors