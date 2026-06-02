# Spec: Profile Page Design

## Overview

The profile page allows logged-in users to view their account information, including name, email, and account creation date. This feature provides a personal dashboard for users to manage their Spendly account and serves as a foundation for future enhancements such as profile editing and settings. It is implemented after the login/logout functionality to ensure only authenticated users can access their profile.

## Depends on

This feature depends on the completion of step 03 (Login and Logout) as it requires the user to be authenticated via session management.

## Routes

- `GET /profile` — displays the user's profile information — access level: logged-in

*Note: The existing `/profile` route in `app.py` will be modified to render a template instead of returning a placeholder string.*

## Database changes

No database changes. The feature utilizes the existing `users` table columns (`name`, `email`, `created_at`) to display user information.

## Templates

- **Create:** `templates/profile.html`
- **Modify:** `templates/base.html` — update the navigation bar to show profile and logout links when a user is logged in, and show sign-in/get-started links when logged out.

## Files to change

- `app.py` — modify the `profile()` function to render `profile.html` and pass user data from the session.
- `templates/base.html` — update navigation links based on authentication state.

## Files to create

- `templates/profile.html`

## New dependencies

No new dependencies. The feature uses existing Flask and Werkzeug packages.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (already implemented in login/registration)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done

- [ ] The `/profile` route renders the `profile.html` template when accessed by a logged-in user.
- [ ] The profile page displays the logged-in user's name, email, and account creation date.
- [ ] The navigation bar in `base.html` shows "Profile" and "Logout" links when a user is logged in.
- [ ] The navigation bar shows "Sign in" and "Get started" links when a user is logged out.
- [ ] Accessing `/profile` without being logged in redirects the user to the login page.
- [ ] The profile page extends `base.html` and uses CSS variables for styling (no hardcoded hex values).
- [ ] No SQLAlchemy or ORMs are used; database interactions (if any) use parameterised queries.
- [ ] The implementation follows the existing code style and conventions in the project.