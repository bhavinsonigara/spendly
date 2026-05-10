from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "dev-secret-key-spendly"

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

    return redirect(url_for("landing"))


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
    app.run(debug=True, port=5001)
