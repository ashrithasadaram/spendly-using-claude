from flask import Flask, render_template, request, redirect, url_for, session
from database.db import init_db, seed_db, get_db
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # In production, use environment variable


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validation
        error = None
        if not name:
            error = "Name is required."
        elif not email:
            error = "Email is required."
        elif not password:
            error = "Password is required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        else:
            # Basic email validation (can be improved)
            if "@" not in email or "." not in email.split("@")[-1]:
                error = "Invalid email address."

        if error is None:
            conn = get_db()
            try:
                cursor = conn.cursor()
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone() is not None:
                    error = "Email already registered."
                else:
                    # Hash password
                    from werkzeug.security import generate_password_hash
                    password_hash = generate_password_hash(password)
                    # Insert user
                    cursor.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, password_hash)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    # Redirect to login page
                    return redirect(url_for("login"))
            except Exception as e:
                conn.rollback()
                error = f"Registration error: {e}"
            finally:
                conn.close()
        # If we have an error, render the template with error
        return render_template("register.html", error=error)

    # GET request
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validation
        error = None
        if not email:
            error = "Email is required."
        elif not password:
            error = "Password is required."

        if error is None:
            conn = get_db()
            try:
                cursor = conn.cursor()
                # Find user by email
                cursor.execute("SELECT id, name, password_hash FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()

                if user is not None:
                    # Verify password
                    from werkzeug.security import check_password_hash
                    if check_password_hash(user['password_hash'], password):
                        # Login successful
                        session['user_id'] = user['id']
                        session['user_name'] = user['name']
                        return redirect(url_for('dashboard'))  # Changed to dashboard
                    else:
                        error = "Invalid email or password."
                else:
                    error = "Invalid email or password."
            except Exception as e:
                error = f"Login error: {e}"
            finally:
                conn.close()

        # If we have an error, render the template with error
        return render_template("login.html", error=error)

    # GET request
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Authenticated Routes                                                #
# ------------------------------------------------------------------ #

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard showing quick links to expense features"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()
        # Get quick stats for dashboard
        cursor.execute(
            """SELECT
                   COUNT(*) as count,
                   SUM(amount) as total
               FROM expenses
               WHERE user_id = ?""",
            (user_id,)
        )
        quick_stats = cursor.fetchone()

        # Get recent expenses
        cursor.execute(
            """SELECT id, amount, category, date, description
               FROM expenses
               WHERE user_id = ?
               ORDER BY date DESC, created_at DESC
               LIMIT 5""",
            (user_id,)
        )
        recent_expenses = cursor.fetchall()

        return render_template("dashboard.html",
                             quick_stats=quick_stats,
                             recent_expenses=recent_expenses)
    except Exception as e:
        return render_template("error.html", error="Unable to load dashboard"), 500
    finally:
        conn.close()


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for('landing'))


@app.route("/profile")
@login_required
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get date filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Set default date range (last 30 days) if not provided
    if not start_date and not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    elif not start_date:
        start_date = end_date
    elif not end_date:
        end_date = start_date

    # Validate date range (ensure start_date <= end_date)
    if start_date > end_date:
        # Swap dates if start is after end
        start_date, end_date = end_date, start_date

    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get user information
        cursor.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (session['user_id'],)
        )
        user = cursor.fetchone()

        if user is None:
            # If user not found, clear session and redirect to login
            session.clear()
            return redirect(url_for('login'))

        # Get expense summary for the date range
        cursor.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expenses WHERE user_id = ? AND date >= ? AND date <= ?",
            (session['user_id'], start_date, end_date)
        )
        summary = cursor.fetchone()

        # Get recent expenses for the date range (limit 5)
        cursor.execute(
            """SELECT id, amount, category, date, description
               FROM expenses
               WHERE user_id = ? AND date >= ? AND date <= ?
               ORDER BY date DESC, created_at DESC
               LIMIT 5""",
            (session['user_id'], start_date, end_date)
        )
        recent_expenses = cursor.fetchall()

        return render_template("profile.html",
                              user=user,
                              summary=summary,
                              recent_expenses=recent_expenses,
                              start_date=start_date,
                              end_date=end_date)
    except Exception as e:
        return render_template("error.html", error="Unable to load profile"), 500
    finally:
        conn.close()


# ================================================================== #
# ANALYTICS (placeholder — coming soon)                               #
# ================================================================== #

@app.route("/analytics")
@login_required
def analytics():
    """Analytics placeholder — deeper insights coming soon."""
    return render_template("analytics.html")


# ================================================================== #
# SUBAGENT 1: TRANSACTION HISTORY ROUTES                             #
# ================================================================== #

@app.route("/expenses")
@login_required
def expenses():
    """List all expenses for current user with optional filtering"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Build query with optional filters
        query = "SELECT id, amount, category, date, description, created_at FROM expenses WHERE user_id = ?"
        params = [user_id]

        # Date filtering
        start_date = request.args.get('start_date')
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        end_date = request.args.get('end_date')
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        # Category filtering
        category = request.args.get('category')
        if category:
            query += " AND category = ?"
            params.append(category)

        # Order and limit
        query += " ORDER BY date DESC, created_at DESC"

        limit = request.args.get('limit')
        if limit:
            try:
                limit = int(limit)
                if limit > 0:
                    query += " LIMIT ?"
                    params.append(limit)
            except ValueError:
                pass  # Ignore invalid limit

        offset = request.args.get('offset')
        if offset:
            try:
                offset = int(offset)
                if offset >= 0:
                    query += " OFFSET ?"
                    params.append(offset)
            except ValueError:
                pass  # Ignore invalid offset

        cursor.execute(query, params)
        expenses = cursor.fetchall()

        # Get distinct categories for filter dropdown
        cursor.execute(
            "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category",
            (user_id,)
        )
        categories = [row['category'] for row in cursor.fetchall()]

        return render_template("expenses.html", expenses=expenses, categories=categories)
    except Exception as e:
        return render_template("error.html", error="Unable to load expenses"), 500
    finally:
        conn.close()


@app.route("/expenses/<int:id>")
@login_required
def expense_detail(id):
    """View specific expense details"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, amount, category, date, description, created_at FROM expenses WHERE id = ? AND user_id = ?",
            (id, user_id)
        )
        expense = cursor.fetchone()

        if expense is None:
            return render_template("error.html", error="Expense not found"), 404

        return render_template("expense_detail.html", expense=expense)
    except Exception as e:
        return render_template("error.html", error="Unable to load expense"), 500
    finally:
        conn.close()


@app.route("/expenses/recent")
@login_required
def expenses_recent():
    """View recent expenses (last 10)"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, amount, category, date, description, created_at
               FROM expenses
               WHERE user_id = ?
               ORDER BY date DESC, created_at DESC
               LIMIT 10""",
            (user_id,)
        )
        expenses = cursor.fetchall()
        return render_template("expenses_recent.html", expenses=expenses)
    except Exception as e:
        return render_template("error.html", error="Unable to load recent expenses"), 500
    finally:
        conn.close()


# ================================================================== #
# SUBAGENT 2: SUMMARY STATISTICS ROUTES                              #
# ================================================================== #

@app.route("/expenses/summary")
@login_required
def expenses_summary():
    """Overall expense summary"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get overall statistics
        cursor.execute(
            """SELECT
                   COUNT(*) as count,
                   SUM(amount) as total,
                   AVG(amount) as average,
                   MIN(amount) as minimum,
                   MAX(amount) as maximum
               FROM expenses
               WHERE user_id = ?""",
            (user_id,)
        )
        stats = cursor.fetchone()

        # Get date range
        cursor.execute(
            """SELECT
                   MIN(date) as start_date,
                   MAX(date) as end_date
               FROM expenses
               WHERE user_id = ?""",
            (user_id,)
        )
        date_range = cursor.fetchone()

        return render_template(
            "expenses_summary.html",
            stats=stats,
            date_range=date_range
        )
    except Exception as e:
        return render_template("error.html", error="Unable to load summary"), 500
    finally:
        conn.close()


@app.route("/expenses/summary/monthly")
@login_required
def expenses_summary_monthly():
    """Monthly expense breakdown"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Group by month (YYYY-MM format from date string)
        cursor.execute(
            """SELECT
                   substr(date, 1, 7) as month,
                   COUNT(*) as count,
                   SUM(amount) as total
               FROM expenses
               WHERE user_id = ?
               GROUP BY substr(date, 1, 7)
               ORDER BY month DESC""",
            (user_id,)
        )
        monthly_data = cursor.fetchall()

        return render_template(
            "expenses_summary_monthly.html",
            monthly_data=monthly_data
        )
    except Exception as e:
        return render_template("error.html", error="Unable to load monthly summary"), 500
    finally:
        conn.close()


@app.route("/expenses/summary/category")
@login_required
def expenses_summary_category():
    """Expense summary by category"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Group by category
        cursor.execute(
            """SELECT
                   category,
                   COUNT(*) as count,
                   SUM(amount) as total,
                   AVG(amount) as average
               FROM expenses
               WHERE user_id = ?
               GROUP BY category
               ORDER BY total DESC""",
            (user_id,)
        )
        category_data = cursor.fetchall()

        return render_template(
            "expenses_summary_category.html",
            category_data=category_data
        )
    except Exception as e:
        return render_template("error.html", error="Unable to load category summary"), 500
    finally:
        conn.close()


# ================================================================== #
# SUBAGENT 3: CATEGORY BREAKDOWN ROUTES                              #
# ================================================================== #

@app.route("/expenses/categories")
@login_required
def categories_overview():
    """Category overview with spending totals"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get all categories with stats
        cursor.execute(
            """SELECT
                   category,
                   COUNT(*) as expense_count,
                   SUM(amount) as total_amount,
                   AVG(amount) as avg_amount,
                   MIN(date) as first_expense,
                   MAX(date) as last_expense
               FROM expenses
               WHERE user_id = ?
               GROUP BY category
               ORDER BY total_amount DESC""",
            (user_id,)
        )
        categories = cursor.fetchall()

        return render_template(
            "categories_overview.html",
            categories=categories
        )
    except Exception as e:
        return render_template("error.html", error="Unable to load categories"), 500
    finally:
        conn.close()


@app.route("/expenses/categories/<string:category>")
@login_required
def category_detail(category):
    """Detail view for specific category"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get category info
        cursor.execute(
            """SELECT
                   COUNT(*) as expense_count,
                   SUM(amount) as total_amount,
                   AVG(amount) as avg_amount,
                   MIN(amount) as min_amount,
                   MAX(amount) as max_amount
               FROM expenses
               WHERE user_id = ? AND category = ?""",
            (user_id, category)
        )
        stats = cursor.fetchone()

        if stats['expense_count'] == 0:
            return render_template("error.html", error="Category not found"), 404

        # Get expenses in this category
        cursor.execute(
            """SELECT
                   id, amount, date, description, created_at
               FROM expenses
               WHERE user_id = ? AND category = ?
               ORDER BY date DESC""",
            (user_id, category)
        )
        expenses = cursor.fetchall()

        return render_template(
            "category_detail.html",
            category=category,
            stats=stats,
            expenses=expenses
        )
    except Exception as e:
        return render_template("error.html", error="Unable to load category details"), 500
    finally:
        conn.close()


@app.route("/expenses/categories/trend")
@login_required
def categories_trend():
    """Category spending trends over time"""
    user_id = session.get('user_id')
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get monthly spending by category for the last 12 months
        cursor.execute(
            """SELECT
                   substr(date, 1, 7) as month,
                   category,
                   SUM(amount) as total
               FROM expenses
               WHERE user_id = ?
                   AND date >= date('now', '-12 months')
               GROUP BY substr(date, 1, 7), category
               ORDER BY month DESC, category""",
            (user_id,)
        )
        trend_data = cursor.fetchall()

        # Get all unique categories for the legend
        cursor.execute(
            """SELECT DISTINCT category
               FROM expenses
               WHERE user_id = ?
               ORDER BY category""",
            (user_id,)
        )
        categories = [row['category'] for row in cursor.fetchall()]

        return render_template(
            "categories_trend.html",
            trend_data=trend_data,
            categories=categories
        )
    except Exception as e:
        return render_template("error.html", error="Unable to load category trends"), 500
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #


@app.route("/expenses/add")
@login_required
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
@login_required
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
@login_required
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)