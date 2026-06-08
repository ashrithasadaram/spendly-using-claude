---
# Spec: Backend Routes for Profile Page

## Overview

This feature implements backend routes for profile management in the Spendly expense tracker, allowing authenticated users to view and update their profile information. It depends on the authentication system (login/logout) and database setup to ensure secure access to user data. Users can view their profile details and update their name and email address, with proper validation and error handling.

## Depends on

- 01-database-setup (users table must exist with proper schema)
- 02-registration (users must be able to register)
- 03-login-logout (users must be able to log in and have sessions)

## Routes

- GET /profile — display user profile information — access level: logged-in
- POST /profile/update — handle profile update form submission, validate and update user information — access level: logged-in
- GET /profile/edit — display profile edit form — access level: logged-in

Note: The existing GET /profile route may need to be enhanced from its placeholder implementation to properly fetch and display user data from the database.

## Database changes

No database changes — the users table already contains the necessary fields (name, email) for profile management.

## Templates

- **Create:** 
  - templates/profile.html — display user profile information
  - templates/profile_edit.html — form for editing profile information
- **Modify:**
  - None (if templates are created as specified above)

## Files to change

- app.py — modify the profile route to properly fetch user data, add profile update route, add profile edit route
- database/db.py — potentially add helper functions for updating user information (optional, can be done directly in routes)

## Files to create

- templates/profile.html — template to display user profile
- templates/profile_edit.html — template for editing profile information

## New dependencies

- No new dependencies (uses existing Flask and werkzeug)

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- When updating email, ensure uniqueness constraint is handled gracefully
- Passwords should not be updated via profile routes (separate security-sensitive process)
- Use CSS variables — never hardcode hex values
- All templates extend base.html
- Validate input: name and email are required, email must be valid format
- On successful update, show success message and redirect to profile view
- On failure, re-display form with error messages
- Ensure user can only edit their own profile (session validation)
- Do not expose password_hash or other sensitive data in templates

## Definition of done

- [ ] User can access /profile page when logged in and see their name, email, and account creation date
- [ ] User can access /profile/edit page when logged in and see a form with their current profile information
- [ ] Submitting the profile edit form with valid data updates the user's information in the database
- [ ] Submitting the form with invalid data (missing fields, invalid email) shows appropriate error messages
- [ ] Attempting to update email to an already-existing email shows an error message
- [ ] Upon successful profile update, user is redirected to /profile page with success indication
- [ ] Password hash is never exposed in templates or logs
- [ ] Application starts without errors
- [ ] No SQL injection vulnerabilities (parameterized queries used)
- [ ] User cannot edit another user's profile (proper session validation)