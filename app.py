from flask import Flask, render_template, request, redirect, url_for, session
from database.db import init_db, seed_db, get_db

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # In production, use environment variable


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
                        return redirect(url_for('landing'))
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
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/dashboard")
def dashboard():
    return "Dashboard — coming in Step 4"


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for('landing'))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
