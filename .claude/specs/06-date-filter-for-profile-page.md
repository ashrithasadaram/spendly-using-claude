---
# Spec: Date Filter for Profile Page

## Overview

This feature enhances the profile page to display expense summary and recent expenses with date filtering capabilities. Users will be able to filter their expense data shown on the profile page by date range, allowing them to review their spending patterns for specific periods. This builds upon the profile management routes implemented in step 05 and leverages the existing date filtering functionality from the expenses route.

## Depends on

- 01-database-setup (users and expense tables must exist)
- 02-registration (users must be able to register)
- 03-login-logout (users must be able to log in and have sessions)
- 05-backend-routes-for-profile-page (profile routes must exist)

## Routes

- No new routes required
- Existing profile routes will be enhanced:
  - GET /profile — display user profile information with expense summary and date-filtered recent expenses — access level: logged-in

## Database changes

No database changes — the existing users and expenses tables contain all necessary fields.

## Templates

- **Create:** None
- **Modify:**
  - templates/profile.html — enhance to show expense summary, date filter form, and date-filtered recent expenses

## Files to change

- app.py — modify the profile route to:
  - Accept date filter parameters (start_date, end_date) via GET
  - Fetch expense summary statistics (count, total, average) for the date range
  - Fetch recent expenses for the date range (with limit)
  - Pass this data to the template
- templates/profile.html — add date filter form and display expense summary and filtered recent expenses

## Files to create

- None

## New dependencies

- No new dependencies (uses existing Flask and sqlite3)

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Use CSS variables — never hardcode hex values
- All templates extend base.html
- Dates must be in YYYY-MM-DD format
- Default behavior when no dates specified: show last 30 days of expenses
- Validate date parameters: ensure start_date ≤ end_date if both provided
- Handle invalid dates gracefully by showing all expenses or resetting to default
- Escape all user data in templates to prevent XSS
- Use LIMIT and OFFSET for efficient querying of recent expenses

## Definition of done

- [ ] User can access /profile page when logged in
- [ ] Profile page shows user's name, email, and account creation date
- [ ] Profile page shows expense summary statistics (total count and amount) for selected date range
- [ ] Profile page shows a date filter form with start_date and end_date inputs
- [ ] Submitting the date filter form updates the displayed expense summary and recent expenses
- [ ] When no dates are specified, defaults to showing last 30 days of expenses
- [ ] Profile page shows recent expenses (limited to 5) for the selected date range
- [ ] Invalid date ranges (start_date after end_date) are handled gracefully
- [ ] Application starts without errors
- [ ] No SQL injection vulnerabilities (parameterized queries used)
- [ ] User can only see their own expense data (proper session validation)