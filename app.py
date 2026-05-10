import datetime

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "dev-secret-key-spendly"

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

PRESETS = {
    "today":        "Today",
    "this_week":    "This Week",
    "last_week":    "Last Week",
    "this_month":   "This Month",
    "last_month":   "Last Month",
    "last_3_months": "Last 3 Months",
}


def _date_range_for_preset(preset):
    today = datetime.date.today()
    if preset == "today":
        return str(today), str(today)
    if preset == "this_week":
        start = today - datetime.timedelta(days=today.weekday())
        return str(start), str(today)
    if preset == "last_week":
        start = today - datetime.timedelta(days=today.weekday() + 7)
        return str(start), str(start + datetime.timedelta(days=6))
    if preset == "this_month":
        return str(today.replace(day=1)), str(today)
    if preset == "last_month":
        last_day = today.replace(day=1) - datetime.timedelta(days=1)
        return str(last_day.replace(day=1)), str(last_day)
    if preset == "last_3_months":
        return str(today - datetime.timedelta(days=90)), str(today)
    return None, None

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("register.html")

    if session.get("user_id"):
        return redirect(url_for("landing"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    db = get_db()
    try:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return render_template("register.html", error="An account with that email already exists.")

        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
    finally:
        db.close()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="All fields are required.")

    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
    finally:
        db.close()

    return redirect(url_for("expenses"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    db = get_db()
    try:
        user = db.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()
    finally:
        db.close()
    return render_template("profile.html", user=user)


@app.route("/profile/update-name", methods=["POST"])
def update_name():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    name = request.form.get("name", "").strip()
    if not name:
        db = get_db()
        try:
            user = db.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
        finally:
            db.close()
        return render_template("profile.html", user=user, name_error="Name cannot be blank.")
    if len(name) > 100:
        db = get_db()
        try:
            user = db.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
        finally:
            db.close()
        return render_template("profile.html", user=user, name_error="Name must be 100 characters or fewer.")
    db = get_db()
    try:
        db.execute("UPDATE users SET name = ? WHERE id = ?", (name, session["user_id"]))
        db.commit()
    finally:
        db.close()
    session["user_name"] = name
    return redirect(url_for("profile") + "?updated=name")


@app.route("/profile/update-password", methods=["POST"])
def update_password():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    def render_with_error(msg):
        db = get_db()
        try:
            user = db.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
        finally:
            db.close()
        return render_template("profile.html", user=user, password_error=msg)

    if not current_password or not new_password or not confirm_password:
        return render_with_error("All fields are required.")
    if len(new_password) < 8:
        return render_with_error("New password must be at least 8 characters.")
    if new_password != confirm_password:
        return render_with_error("Passwords do not match.")

    db = get_db()
    try:
        row = db.execute(
            "SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        if not check_password_hash(row["password_hash"], current_password):
            return render_with_error("Current password is incorrect.")
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), session["user_id"]),
        )
        db.commit()
    finally:
        db.close()
    return redirect(url_for("profile") + "?updated=password")


@app.route("/expenses")
def expenses():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    preset = request.args.get("preset", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # Preset overrides any manual date inputs
    sql_from, sql_to = date_from, date_to
    if preset in PRESETS:
        sql_from, sql_to = _date_range_for_preset(preset)

    query = ("SELECT id, amount, category, date, description FROM expenses"
             " WHERE user_id = ?")
    params = [session["user_id"]]
    if sql_from:
        query += " AND date >= ?"
        params.append(sql_from)
    if sql_to:
        query += " AND date <= ?"
        params.append(sql_to)
    query += " ORDER BY date DESC, id DESC"

    db = get_db()
    try:
        rows = db.execute(query, params).fetchall()
    finally:
        db.close()

    total = sum(e["amount"] for e in rows)
    by_category = {}
    for e in rows:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]
    return render_template(
        "expenses.html",
        expenses=rows,
        total=total,
        by_category=by_category,
        categories=CATEGORIES,
        presets=PRESETS,
        preset=preset,
        date_from=date_from,
        date_to=date_to,
    )


def _expenses_context(user_id):
    db = get_db()
    try:
        rows = db.execute(
            "SELECT id, amount, category, date, description FROM expenses"
            " WHERE user_id = ? ORDER BY date DESC, id DESC",
            (user_id,),
        ).fetchall()
    finally:
        db.close()
    total = sum(e["amount"] for e in rows)
    by_category = {}
    for e in rows:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]
    return {
        "expenses": rows,
        "total": total,
        "by_category": by_category,
        "categories": CATEGORIES,
        "presets": PRESETS,
        "preset": "",
        "date_from": "",
        "date_to": "",
    }


def _validate_expense_form(amount_str, category, date_str, description):
    if not amount_str or not category or not date_str:
        return None, None, None, "Amount, category, and date are required."
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return None, None, None, "Amount must be a positive number."
    if category not in CATEGORIES:
        return None, None, None, "Invalid category selected."
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        return None, None, None, "Date must be in YYYY-MM-DD format."
    if description and len(description) > 200:
        return None, None, None, "Description must be 200 characters or fewer."
    return amount, category, date_str, None


@app.route("/expenses/add", methods=["POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    amount, category, date_str, error = _validate_expense_form(amount_str, category, date_str, description)
    if error:
        return render_template("expenses.html", add_error=error, **_expenses_context(session["user_id"]))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], amount, category, date_str, description or None),
        )
        db.commit()
    finally:
        db.close()
    return redirect(url_for("expenses"))


@app.route("/expenses/<int:id>/edit", methods=["POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    amount, category, date_str, error = _validate_expense_form(amount_str, category, date_str, description)
    if error:
        return render_template("expenses.html", edit_error=error, edit_id=id, **_expenses_context(session["user_id"]))

    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM expenses WHERE id = ? AND user_id = ?",
            (id, session["user_id"]),
        ).fetchone()
        if not existing:
            return redirect(url_for("expenses"))
        db.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ?"
            " WHERE id = ? AND user_id = ?",
            (amount, category, date_str, description or None, id, session["user_id"]),
        )
        db.commit()
    finally:
        db.close()
    return redirect(url_for("expenses"))


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))
    db = get_db()
    try:
        db.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (id, session["user_id"]),
        )
        db.commit()
    finally:
        db.close()
    return redirect(url_for("expenses"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
