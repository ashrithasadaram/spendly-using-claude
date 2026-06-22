import pytest
from datetime import datetime, timedelta
from database.db import get_db


# ------------------------------------------------------------------ #
# Fixtures — mirror tests/test_06-date-filter-for-profile-page.py     #
# ------------------------------------------------------------------ #

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
    """A logged-in test client (registers + logs in 'test@example.com')."""
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    })
    return client


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def insert_expense(user_id, amount, category, date_str, description=''):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date_str, description)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_id_by_email(email):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return row['id'] if row else None
    finally:
        conn.close()


def count_expenses(user_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]
    finally:
        conn.close()


def get_latest_expense(user_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, amount, category, date, description "
            "FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# Test classes                                                         #
# ------------------------------------------------------------------ #

class TestAddExpenseAccess:
    def test_unauthenticated_get_redirects_to_login(self, client):
        """GET /expenses/add without session must redirect to /login."""
        response = client.get('/expenses/add')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_authenticated_get_renders_form(self, auth_client):
        """GET /expenses/add when logged in returns 200 with the form fields."""
        response = auth_client.get('/expenses/add')
        assert response.status_code == 200
        assert b'name="amount"' in response.data
        assert b'name="category"' in response.data
        assert b'name="date"' in response.data
        assert b'name="description"' in response.data
        # The auth-card / form wrapper is rendered
        assert b'auth-card' in response.data
        # All seven allowed categories are present
        for cat in ('Food', 'Transport', 'Bills', 'Health',
                    'Entertainment', 'Shopping', 'Other'):
            assert cat.encode() in response.data

    def test_get_does_not_insert_row(self, auth_client):
        """A GET must not insert any rows into the expenses table."""
        user_id = get_user_id_by_email('test@example.com')
        before = count_expenses(user_id)
        auth_client.get('/expenses/add')
        after = count_expenses(user_id)
        assert before == after


class TestAddExpenseSuccess:
    def test_valid_post_inserts_row_and_redirects_to_dashboard(self, auth_client):
        """A valid POST inserts a row and 302-redirects to /dashboard."""
        user_id = get_user_id_by_email('test@example.com')
        before = count_expenses(user_id)
        response = auth_client.post('/expenses/add', data={
            'amount': '42.50',
            'category': 'Food',
            'date': '2026-06-21',
            'description': 'Pizza with the team',
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard' in response.location
        after = count_expenses(user_id)
        assert after == before + 1

    def test_row_is_scoped_to_logged_in_user(self, auth_client):
        """The inserted row's user_id matches session['user_id']."""
        user_id = get_user_id_by_email('test@example.com')
        auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Transport',
            'date': '2026-06-21',
            'description': 'Bus ticket',
        })
        row = get_latest_expense(user_id)
        assert row is not None
        assert row['user_id'] == user_id
        assert row['amount'] == 10.0
        assert row['category'] == 'Transport'
        assert row['date'] == '2026-06-21'
        assert row['description'] == 'Bus ticket'

    def test_valid_post_with_empty_description(self, auth_client):
        """A valid POST with no description still inserts the row."""
        user_id = get_user_id_by_email('test@example.com')
        before = count_expenses(user_id)
        response = auth_client.post('/expenses/add', data={
            'amount': '5.00',
            'category': 'Other',
            'date': '2026-06-21',
            'description': '',
        })
        assert response.status_code == 302
        assert count_expenses(user_id) == before + 1
        row = get_latest_expense(user_id)
        assert row['description'] == ''

    def test_inserted_expense_appears_on_dashboard(self, auth_client):
        """An inserted expense is visible on the /dashboard recent activity list."""
        auth_client.post('/expenses/add', data={
            'amount': '99.00',
            'category': 'Shopping',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': 'New sneakers',
        })
        response = auth_client.get('/dashboard')
        assert response.status_code == 200
        assert b'New sneakers' in response.data

    def test_inserted_expense_appears_on_expenses_list(self, auth_client):
        """An inserted expense is visible on /expenses."""
        auth_client.post('/expenses/add', data={
            'amount': '12.00',
            'category': 'Bills',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': 'Water bill',
        })
        response = auth_client.get('/expenses')
        assert response.status_code == 200
        assert b'Water bill' in response.data

    def test_inserted_expense_appears_on_profile(self, auth_client):
        """An inserted expense is visible on /profile within the default 30-day range."""
        auth_client.post('/expenses/add', data={
            'amount': '7.50',
            'category': 'Health',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': 'Pharmacy run',
        })
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Pharmacy run' in response.data


class TestAddExpenseAmountValidation:
    def test_missing_amount_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '',
            'category': 'Food',
            'date': '2026-06-21',
            'description': 'No amount',
        })
        assert response.status_code == 200
        assert b'Amount is required' in response.data

    def test_non_numeric_amount_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': 'abc',
            'category': 'Food',
            'date': '2026-06-21',
            'description': 'Garbage amount',
        })
        assert response.status_code == 200
        assert b'must be a number' in response.data
        # The raw text is preserved in the rendered input
        assert b'value="abc"' in response.data

    def test_zero_amount_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '0',
            'category': 'Food',
            'date': '2026-06-21',
            'description': 'Zero amount',
        })
        assert response.status_code == 200
        assert b'greater than 0' in response.data

    def test_negative_amount_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '-5',
            'category': 'Food',
            'date': '2026-06-21',
            'description': 'Negative amount',
        })
        assert response.status_code == 200
        assert b'greater than 0' in response.data
        assert b'value="-5"' in response.data

    def test_invalid_amount_does_not_insert_row(self, auth_client):
        user_id = get_user_id_by_email('test@example.com')
        before = count_expenses(user_id)
        auth_client.post('/expenses/add', data={
            'amount': 'abc',
            'category': 'Food',
            'date': '2026-06-21',
            'description': 'Should not save',
        })
        assert count_expenses(user_id) == before


class TestAddExpenseCategoryValidation:
    def test_missing_category_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': '',
            'date': '2026-06-21',
            'description': 'No category',
        })
        assert response.status_code == 200
        assert b'Category is required' in response.data

    def test_unsupported_category_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Bogus',
            'date': '2026-06-21',
            'description': 'Bad category',
        })
        assert response.status_code == 200
        assert b'valid category' in response.data

    def test_category_matching_is_case_sensitive(self, auth_client):
        """Lowercase 'food' is rejected; only the exact 'Food' is accepted."""
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'food',
            'date': '2026-06-21',
            'description': 'Wrong case',
        })
        assert response.status_code == 200
        assert b'valid category' in response.data


class TestAddExpenseDateValidation:
    def test_missing_date_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': '',
            'description': 'No date',
        })
        assert response.status_code == 200
        assert b'Date is required' in response.data

    def test_malformed_date_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': '2026-13-01',
            'description': 'Bad month',
        })
        assert response.status_code == 200
        assert b'YYYY-MM-DD' in response.data

    def test_us_style_date_shows_error(self, auth_client):
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': '06/21/2026',
            'description': 'US format',
        })
        assert response.status_code == 200
        assert b'YYYY-MM-DD' in response.data


class TestAddExpenseDescriptionValidation:
    def test_description_at_max_length_accepted(self, auth_client):
        user_id = get_user_id_by_email('test@example.com')
        before = count_expenses(user_id)
        desc = 'x' * 255
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': '2026-06-21',
            'description': desc,
        })
        assert response.status_code == 302
        assert count_expenses(user_id) == before + 1

    def test_description_over_max_length_rejected(self, auth_client):
        user_id = get_user_id_by_email('test@example.com')
        before = count_expenses(user_id)
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': '2026-06-21',
            'description': 'x' * 256,
        })
        assert response.status_code == 200
        assert b'255 characters or fewer' in response.data
        assert count_expenses(user_id) == before


class TestAddExpenseSecurity:
    def test_sql_injection_in_description_is_safe(self, auth_client):
        """SQL-injection attempts are stored as literal text; table remains intact."""
        user_id = get_user_id_by_email('test@example.com')
        payload = "'; DROP TABLE expenses;--"
        response = auth_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': '2026-06-21',
            'description': payload,
        })
        assert response.status_code == 302
        # expenses table still exists
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM expenses")
            assert cursor.fetchone()[0] >= 1
        finally:
            conn.close()
        # The latest row's description is the literal payload
        row = get_latest_expense(user_id)
        assert row['description'] == payload
