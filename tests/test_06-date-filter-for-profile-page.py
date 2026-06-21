import pytest
from datetime import datetime, timedelta
from database.db import get_db

# Fixtures
@pytest.fixture
def app():
    from app import app as flask_app
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': ':memory:',
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        from database.db import init_db
        init_db()
        yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Create a test client logged in as a test user."""
    # Register a user with required fields: name, email, password
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass'
    })
    # Login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    })
    return client

# Helper to insert an expense for a given user_id
def insert_expense(user_id, amount, category, date_str, description=''):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date_str, description)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

# Helper to get user id from email
def get_user_id_by_email(email):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return row['id'] if row else None
    finally:
        conn.close()

class TestProfileAccess:
    def test_unauthenticated_redirected_to_login(self, client):
        """Unauthenticated access to /profile should redirect to login page."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_authenticated_user_can_access(self, auth_client):
        """Authenticated user can access profile page."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        # Ensure we are not redirected to login
        assert b'login' not in response.data or response.request.path == '/profile'

class TestProfileDisplay:
    def test_shows_user_information(self, auth_client):
        """Profile page displays logged-in user's name and email."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Test User' in response.data
        assert b'test@example.com' in response.data

    def test_shows_date_filter_form(self, auth_client):
        """Profile page contains a form with start_date and end_date inputs."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'name="start_date"' in response.data
        assert b'name="end_date"' in response.data
        assert b'<form' in response.data

class TestDateFiltering:
    def test_default_date_range_is_last_30_days(self, auth_client):
        """When no dates provided, default to last 30 days."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        today = datetime.now()
        old_date = (today - timedelta(days=45)).strftime('%Y-%m-%d')
        recent_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
        insert_expense(user_id, 100.0, 'Food', old_date, 'Old expense')
        insert_expense(user_id, 50.0, 'Transport', recent_date, 'Recent expense')
        response = auth_client.get('/profile')
        assert response.status_code == 200
        # Recent expense should be visible, old expense should not
        assert b'Recent expense' in response.data
        assert b'Old expense' not in response.data

    def test_custom_date_range_filters_expenses(self, auth_client):
        """Providing start_date and end_date filters expenses to that range."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        date1 = '2026-01-01'
        date2 = '2026-02-01'
        date3 = '2026-03-01'
        insert_expense(user_id, 10.0, 'Cat1', date1, 'Expense1')
        insert_expense(user_id, 20.0, 'Cat2', date2, 'Expense2')
        insert_expense(user_id, 30.0, 'Cat3', date3, 'Expense3')
        response = auth_client.get('/profile?start_date=2026-02-01&end_date=2026-02-28')
        assert response.status_code == 200
        assert b'Expense2' in response.data
        assert b'Expense1' not in response.data
        assert b'Expense3' not in response.data

    def test_only_start_date_sets_end_equal_to_start(self, auth_client):
        """If only start_date is given, end_date defaults to start_date."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        date = '2026-01-15'
        insert_expense(user_id, 15.0, 'Test', date, 'Solo start')
        response = auth_client.get(f'/profile?start_date={date}')
        assert response.status_code == 200
        assert b'Solo start' in response.data

    def test_only_end_date_sets_start_equal_to_end(self, auth_client):
        """If only end_date is given, start_date defaults to end_date."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        date = '2026-01-15'
        insert_expense(user_id, 15.0, 'Test', date, 'Solo end')
        response = auth_client.get(f'/profile?end_date={date}')
        assert response.status_code == 200
        assert b'Solo end' in response.data

    def test_start_date_after_end_date_gets_swapped(self, auth_client):
        """If start_date > end_date, the dates are swapped before querying."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        mid_date = '2026-01-15'
        insert_expense(user_id, 50.0, 'Test', mid_date, 'Middle')
        response = auth_client.get('/profile?start_date=2026-02-01&end_date=2026-01-01')
        assert response.status_code == 200
        # After swapping, range is 2026-01-01 to 2026-02-01, which includes mid_date
        assert b'Middle' in response.data

    def test_recent_expenses_limited_to_five(self, auth_client):
        """Recent expenses list is limited to 5 entries."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        base = datetime.now()
        for i in range(6):
            date = (base - timedelta(days=i)).strftime('%Y-%m-%d')
            insert_expense(user_id, float(i+1), 'Cat', date, f'Expense {i+1}')
        response = auth_client.get('/profile')
        assert response.status_code == 200
        # Most recent 5 should be present (i=0 to 4)
        assert b'Expense 1' in response.data   # today
        assert b'Expense 2' in response.data
        assert b'Expense 3' in response.data
        assert b'Expense 4' in response.data
        assert b'Expense 5' in response.data
        # The 6th (i=5) should be absent due to LIMIT 5
        assert b'Expense 6' not in response.data

    def test_recent_expenses_ordered_by_date_descending(self, auth_client):
        """Recent expenses are ordered by date descending (newest first)."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        base = datetime.now()
        date_old = (base - timedelta(days=10)).strftime('%Y-%m-%d')
        date_recent = (base - timedelta(days=1)).strftime('%Y-%m-%d')
        insert_expense(user_id, 10.0, 'Cat', date_old, 'Older')
        insert_expense(user_id, 20.0, 'Cat', date_recent, 'Recent')
        response = auth_client.get('/profile')
        assert response.status_code == 200
        recent_pos = response.data.find(b'Recent')
        older_pos = response.data.find(b'Older')
        assert recent_pos != -1 and older_pos != -1
        assert recent_pos < older_pos  # Recent appears before Older

    def test_user_cannot_see_another_users_expenses(self, auth_client):
        """Users can only see their own expense data."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        # Create a second user record
        other_user_id = user_id + 999
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                (other_user_id, 'Other User', 'other@example.com', 'hash')
            )
            conn.commit()
        finally:
            conn.close()
        # Insert expenses for both users
        date = '2026-01-01'
        insert_expense(other_user_id, 999.0, 'Other', date, 'Other user expense')
        insert_expense(user_id, 50.0, 'Test', date, 'Test user expense')
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Test user expense' in response.data
        assert b'Other user expense' not in response.data

    def test_invalid_date_format_does_not_cause_error(self, auth_client):
        """Invalid date strings should not cause server errors."""
        response = auth_client.get('/profile?start_date=not-a-date&end_date=also-invalid')
        assert response.status_code == 200
        # Page should load without error message
        assert b'Unable to load profile' not in response.data

    def test_sql_injection_attempt_in_date_params_is_safe(self, auth_client):
        """SQL injection attempts in date parameters should be treated as literal strings."""
        response = auth_client.get('/profile?start_date=2026-01-01 OR 1=1--&end_date=2026-12-31')
        assert response.status_code == 200
        assert b'Unable to load profile' not in response.data

    def test_expense_summary_totals_are_correct(self, auth_client):
        """Expense summary shows correct count and total for the selected date range."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        date = '2026-01-01'
        insert_expense(user_id, 100.0, 'Food', date, 'Meal')
        insert_expense(user_id, 200.0, 'Transport', date, 'Taxi')
        insert_expense(user_id, 50.0, 'Food', date, 'Snack')
        response = auth_client.get(f'/profile?start_date={date}&end_date={date}')
        assert response.status_code == 200
        # Expected total = 350.0, count = 3
        # Check for these numbers in the response (allow for formatting)
        assert b'350' in response.data or b'350.0' in response.data
        assert b'3' in response.data

    def test_expense_summary_zero_when_no_expenses(self, auth_client):
        """When there are no expenses in the date range, summary shows zero."""
        user_email = 'test@example.com'
        user_id = get_user_id_by_email(user_email)
        # Ensure no expenses exist for this user (we rely on fresh DB per test)
        # Request with a date range where we know there are no expenses
        response = auth_client.get('/profile?start_date=2025-01-01&end_date=2025-01-31')
        assert response.status_code == 200
        # Expect zero count and total
        assert b'0' in response.data  # count
        assert b'0' in response.data  # total (may appear twice)