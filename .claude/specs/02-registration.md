---

# Spec: Registration

## Overview

This feature implements user registration for the Spendly expense tracker, allowing new users to create an account with a name, email, and password. It depends on the database setup step to ensure the users table exists with proper constraints. The registration form collects user details, validates input, hashes the password, and stores the new user in the database. Upon successful registration, the user is shown with success message and then redirected to the login page.this is the entry point for all authenticated features that follow.

## Depends on

- 01-database-setup (users table must exist)

## Routes

- POST /register — handle registration form submission, create new user, hash password, redirect to login — access level: public
- GET /register — display registration form (existing) — access level: public

Note: The existing GET /register route in app.py will be extended to handle POST requests.

## Database changes

No database changes — the users table was created in step 1.

## Templates

- **Create:** None
- **Modify:**
  - templates/register.html — add form handling for POST, display validation errors, and show success message

## Files to change

- app.py — modify the register route to handle GET and POST, implement registration logic
- templates/register.html — update the form to submit to itself and display errors/messages

## Files to create

- None

## New dependencies

- No new dependencies (uses existing Flask and werkzeug)

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug.security.generate_password_hash
- Use CSS variables — never hardcode hex values (but note: we are not changing CSS in this step, but we'll follow for any new CSS)
- All templates extend base.html (register.html already does)
- Validate input: name, email, email format, password strength (at least 6 characters)
- Ensure email uniqueness (handle database constraint gracefully)
- On success, redirect to login page with a success message (via flash or query parameter)
- On failure, re-display form with error messages

## Definition of done

- [ ] User can access /register page and see the registration form
- [ ] Submitting the form with valid data creates a new user in the database
- [ ] Password is hashed using werkzeug
- [ ] Duplicate email submission shows an error
- [ ] Upon successful registration, user is redirected to /login
- [ ] Form validation works for missing fields, invalid email, short password
- [ ] No SQL injection vulnerabilities (parameterized queries used)
- [ ] Application starts without errors
