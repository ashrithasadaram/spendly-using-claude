# Spec: Edit Expense

## Overview

This feature lets authenticated users edit an expense they previously recorded. It replaces the placeholder `GET /expenses/<id>/edit` route (currently returning the string "Edit expense — coming in Step 8") with a real form-and-POST handler that loads the row, validates the submitted input, updates the row in the `expenses` table, and redirects back to the expense's detail page. Scoping by `session['user_id']` is critical so users can only modify their own expenses — an attempt to edit another user's expense must respond with 404, never 403, to avoid leaking which IDs exist. This step, together with step 07 (Add Expense) and the upcoming step 09 (Delete Expense), closes the expense lifecycle: create → read → update → delete.

## Depends on

- 01-database-setup — the `expenses` table must exist with columns `id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`
- 02-registration — users must exist in the `users` table
- 03-login-logout — users must be able to log in; `session['user_id']` and `session['user_name']` must be available
- 05-backend-routes-for-profile-page — provides `GET /expenses/<id>` (expense_detail) that this feature's "Back to detail" / post-update redirect targets
- 07-add-expense — establishes the `ALLOWED_CATEGORIES` tuple and the validation pattern (amount > 0, category in allow-list, date in `YYYY-MM-DD`, description ≤ 255 chars) that the edit form must reuse so the two forms behave identically

## Routes

- `GET /expenses/<int:id>/edit` — load the expense, confirm it belongs to the logged-in user, render the edit form prefilled with current values — access level: logged-in
- `POST /expenses/<int:id>/edit` — validate submitted input, UPDATE the matching row in `expenses`, redirect to `/expenses/<id>` on success — access level: logged-in

The existing placeholder at `GET /expenses/<int:id>/edit` will be replaced. The new route accepts both GET and POST.

## Database changes

No database changes — the `expenses` table already contains every column this feature needs (`amount`, `category`, `date`, `description`). Only `UPDATE` and `SELECT` queries are issued; no schema migrations.

## Templates

- **Create:**
  - `templates/edit_expense.html` — form mirroring `add_expense.html`: amount, category, date, description fields, plus validation error display. Prefilled with the existing row's values on GET. Header links "Back to detail" and "Cancel".
- **Modify:**
  - `templates/expense_detail.html` — no structural change required (the Edit link is already wired). Confirm the page still renders correctly after the placeholder route is replaced.

## Files to change

- `app.py` — replace the placeholder `edit_expense` route with a real implementation that handles GET (load row scoped by user_id, render form) and POST (validate + UPDATE). Reuse the `ALLOWED_CATEGORIES` tuple and the validation rules from `add_expense`. Return 404 via `error.html` when the row does not exist for the current user.

## Files to create

- `templates/edit_expense.html` — Jinja template that extends `base.html` and renders the edit-expense form, prefilled with the existing expense's values

## New dependencies

No new dependencies — uses the existing Flask, sqlite3, and werkzeug stack.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only (use `?` placeholders, never f-strings in SQL)
- Passwords hashed with werkzeug (not relevant here, but maintain the convention)
- Use CSS variables — never hardcode hex values in any new or modified CSS (the existing edit form should reuse `auth-card`, `form-group`, `form-input`, `btn-submit`, `auth-error` classes — no new CSS needed unless a small adjustment is required)
- All templates extend `base.html`
- Authorisation: every SELECT and UPDATE must include `WHERE id = ? AND user_id = ?` so users can never read or modify another user's expense. If the row is not found for the current user, render `error.html` with HTTP 404 — do not distinguish "not found" from "not yours", to avoid leaking the existence of other users' IDs
- Validation rules (must match `add_expense` exactly so behaviour is consistent):
  - `amount` — required, must parse as a float, must be greater than 0; preserve the raw text on validation failure for re-display
  - `category` — required, must be a member of `ALLOWED_CATEGORIES`; strip whitespace
  - `date` — required, must parse as `YYYY-MM-DD` via `datetime.strptime`
  - `description` — optional, free text; strip whitespace; cap at 255 characters
- Preserve user-supplied form values across POST validation failures (similar to `add_expense`'s `amount_value` / `category_value` / `date_value` / `description_value` pattern) so the user does not lose their input
- On success: `UPDATE` the row, commit, close the connection, redirect to `url_for('expense_detail', id=id)`
- On exception: rollback, close the connection, render `error.html` with HTTP 500
- Wrap DB work in `try / except / finally` so the connection is closed even on errors
- Escape all user-supplied data in the template to prevent XSS (Jinja autoescape is sufficient)
- Do not introduce any new pip packages

## Definition of done

- [ ] GET `/expenses/<id>/edit` when logged in renders the edit form prefilled with the existing row's values
- [ ] GET `/expenses/<id>/edit` when not logged in redirects to `/login`
- [ ] GET `/expenses/<id>/edit` for an expense that does not exist renders `error.html` with HTTP 404
- [ ] GET `/expenses/<id>/edit` for an expense owned by another user renders `error.html` with HTTP 404 (not 403 — do not leak ID existence)
- [ ] Submitting the form with valid amount, category, date, and optional description UPDATEs the matching row in `expenses` for the logged-in user
- [ ] After a successful update the user is redirected to `/expenses/<id>` and the new values are visible on that page
- [ ] Submitting with a missing amount shows a validation error and re-renders the form with the other submitted values preserved
- [ ] Submitting with a non-numeric or non-positive amount shows a validation error and re-renders the form
- [ ] Submitting with a missing or unsupported category shows a validation error and re-renders the form
- [ ] Submitting with a missing or malformed date shows a validation error and re-renders the form
- [ ] Submitting with a description longer than 255 characters shows a validation error and re-renders the form
- [ ] An edited expense immediately reflects the new values on `/dashboard` recent-activity list
- [ ] An edited expense immediately reflects the new values on `/expenses`
- [ ] An edited expense immediately reflects the new values on `/profile` (within the default last-30-days range, or the user's selected range)
- [ ] An attempt to POST to `/expenses/<id>/edit` for another user's expense renders `error.html` with HTTP 404 and does not modify the row
- [ ] No SQL injection vulnerabilities — all queries use parameterised `?` placeholders
- [ ] No hardcoded hex colors — any new CSS uses existing CSS variables
- [ ] Application starts without errors