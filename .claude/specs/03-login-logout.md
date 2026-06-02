---

# Spec: Login and Logout

## Overview

This feature implements user authentication for the Spendly expense tracker, allowing registered users to log in and log out of the application. It depends on the registration feature (step 02) to ensure users exist in the database. The login form validates credentials against the stored hashed password, establishes a user session, and redirects to the expense tracking interface (to be implemented in later steps). The logout endpoint clears the session and redirects to the landing page. This feature is essential for protecting user data and enabling personalized expense tracking.

## Depends on

- 01-Database Setup('Users' table must exist)
- 02-registration (users must be able to register and have hashed passwords in the database)

## Routes

- POST /login — handle login form submission, validate credentials, create user session, redirect to dashboard — access level: public
- GET /login — display login form (existing) — access level: public
- POST /logout — process logout request, clear session, redirect to landing — access level: logged-in

Note: The existing GET /login route in app.py will be extended to handle POST requests. A new route for logout will be added.

## Database changes

No database changes — the users table already includes the necessary password_hash field for authentication.

## Templates

- **Create:** None
- **Modify:**
  - templates/login.html — add form handling for POST, display validation errors, and show success message

## Files to change

- app.py — modify the login route to handle GET and POST, implement login logic; add a new logout route
- templates/login.html — update the form to submit to itself and display errors/messages

## Files to create

- None

## New dependencies

- No new dependencies (uses existing Flask and werkzeug)

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified using werkzeug.security.check_password_hash
- Use CSS variables — never hardcode hex values (but note: we are not changing CSS in this step, but we'll follow for any new CSS)
- All templates extend base.html (login.html already does)
- Use Flask session to manage user state (set session['user_id'] on login, clear on logout)
- Ensure session is secure by using Flask's secret key (to be set in app configuration)
- Validate input: email and password are required
- On successful login, store user's id in session and redirect to a dashboard (to be implemented in later steps; for now, redirect to a placeholder)
- On logout, clear the session and redirect to the landing page
- Handle invalid credentials gracefully with error messages

## Definition of done

- [ ] User can access /login page and see the login form
- [ ] Submitting the form with valid credentials logs the user in and sets a session
- [ ] Password is verified using werkzeug.security.check_password_hash (not compared in plain text)
- [ ] Invalid credentials show an error message
- [ ] Upon successful login, user is redirected to a dashboard page (placeholder for now)
- [ ] Logging out clears the session and redirects to the landing page
- [ ] Access to protected routes (to be implemented) requires login
- [ ] No SQL injection vulnerabilities (parameterized queries used)
- [ ] Application starts without errors
