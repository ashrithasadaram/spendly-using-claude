---
# Spec: Delete Expense

## Overview

This feature lets authenticated users delete an expense they previously recorded. It replaces the placeholder `GET /expenses/<id>/delete` route (currently returning the string "Delete expense — coming in Step 9") with a real `POST` handler that verifies the row belongs to the logged-in user, deletes it from the `expenses` table, and redirects back to the expenses list. The existing `expense_detail.html` template already wires a Delete button to this route via a POST form with a `confirm()` prompt, so the route must accept POST and must be idempotent-friendly. Scoping by `session['user_id']` is critical so users can only delete their own expenses — an attempt to delete another user's expense must respond with 404, never 403, to avoid leaking which IDs exist. This step closes the expense lifecycle alongside step 07 (Add Expense) and step 08 (Edit Expense): create → read → update → delete.

## Depends on

- 01-database-setup — the `expenses` table must exist with columns `id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`
- 02-registration — users must exist in the `users` table
- 03-login-logout — users must be able to log in; `session['user_id']` must be available
- 05-backend-routes-for-profile-page — provides `GET /expenses` (expenses) that this feature's post-delete redirect targets
- 07-add-expense — establishes the expense row format and the `ALLOWED_CATEGORIES` allow-list context
- 08-edit-expense — establishes the same authorisation pattern (`WHERE id = ? AND user_id = ?`, 404 on miss) that this feature must reuse

## Routes

- `POST /expenses/<int:id>/delete` — confirm the expense belongs to the logged-in user, DELETE the matching row from `expenses`, redirect to `/expenses` on success — access level: logged-in
- `GET /expenses/<int:id>/delete` — also wired (see Rules) so a direct URL visit responds with the same 404, never executes a destructive action, and never returns a method-not-allowed page that leaks the route exists — access level: logged-in

The existing placeholder at `GET /expenses/<int:id>/delete` will be replaced. The new route accepts both GET and POST, but only POST performs the delete.

## Database changes

No database changes — the `expenses` table already contains the `id` and `user_id` columns this feature needs. Only `DELETE` and `SELECT` queries are issued; no schema migrations.

## Templates

- **Create:** none
- **Modify:**
  - `templates/expense_detail.html` — no structural change required (the Delete button and its `confirm()` prompt are already wired). Confirm the page still renders correctly after the placeholder route is replaced. No new "Delete" link is required on `expenses.html` (the listing already exposes Edit only — keeping the list clean is intentional, since delete is a destructive action and lives on the detail page).

## Files to change

- `app.py` — replace the placeholder `delete_expense` route with a real implementation that handles POST (load row scoped by user_id, DELETE the row, redirect to `/expenses`) and GET (respond with the same 404 path so direct URL visits do not perform a delete and do not reveal the route). Reuse the same authorisation pattern as `edit_expense`: `WHERE id = ? AND user_id = ?` on every read, and a 404 via `error.html` if the row does not exist for the current user.

## Files to create

None.

## New dependencies

No new dependencies — uses the existing Flask, sqlite3, and werkzeug stack.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only (use `?` placeholders, never f-strings in SQL)
- Passwords hashed with werkzeug (not relevant here, but maintain the convention)
- Use CSS variables — never hardcode hex values in any new or modified CSS (no new CSS is expected — the existing Delete button uses the `btn-danger` class already defined elsewhere)
- All templates extend `base.html` (no template changes required for this step)
- **Method handling:** the route function must accept both `GET` and `POST` (declared with `methods=["GET", "POST"]`). On `GET`, render `error.html` with HTTP 404 — do NOT execute a delete. This protects against CSRF-style GET-based destructive actions and matches the existing `expense_detail.html` which submits via POST.
- **Authorisation:** every SELECT and DELETE must include `WHERE id = ? AND user_id = ?` so users can never read or delete another user's expense. If the row is not found for the current user, render `error.html` with HTTP 404 — do not distinguish "not found" from "not yours", to avoid leaking the existence of other users' IDs
- **Confirmation:** the user already confirms the action in the browser via the `confirm('Are you sure you want to delete this expense?')` dialog in `expense_detail.html`. No additional server-side confirmation page is required for this step.
- On success: DELETE the row, commit, close the connection, redirect to `url_for('expenses')` (the listing page — the user can re-find the row in their full history if they need to)
- On exception: rollback, close the connection, render `error.html` with HTTP 500
- Wrap DB work in `try / except / finally` so the connection is closed even on errors
- Do not introduce any new pip packages

## Definition of done

- [ ] GET `/expenses/<id>/delete` when not logged in redirects to `/login`
- [ ] GET `/expenses/<id>/delete` when logged in renders `error.html` with HTTP 404 (does not delete the row, does not reveal route existence via 405)
- [ ] POST `/expenses/<id>/delete` when not logged in redirects to `/login`
- [ ] POST `/expenses/<id>/delete` for an expense owned by the logged-in user deletes the row and redirects to `/expenses`
- [ ] POST `/expenses/<id>/delete` for an expense that does not exist renders `error.html` with HTTP 404
- [ ] POST `/expenses/<id>/delete` for an expense owned by another user renders `error.html` with HTTP 404 (not 403 — do not leak ID existence) and does not modify the row
- [ ] After a successful delete, the row is no longer visible on `/dashboard` recent-activity list
- [ ] After a successful delete, the row is no longer visible on `/expenses`
- [ ] After a successful delete, the row is no longer visible on `/profile` (within the default last-30-days range, or the user's selected range)
- [ ] After a successful delete, attempting to GET `/expenses/<id>` (expense_detail) renders `error.html` with HTTP 404
- [ ] The Delete button on `/expenses/<id>` still shows a `confirm()` prompt before submitting
- [ ] No SQL injection vulnerabilities — all queries use parameterised `?` placeholders
- [ ] No hardcoded hex colors — any new CSS uses existing CSS variables
- [ ] Application starts without errors
