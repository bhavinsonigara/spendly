import datetime

import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

ADD_URL = "/expenses/add"


def _login(client):
    client.post("/login", data={"email": "test@example.com", "password": "password123"})


def _add_expense(amount=50.0, category="Food", date="2026-05-01",
                 description="Test expense", user_email="test@example.com"):
    conn = db_module.get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", (user_email,)).fetchone()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user["id"], amount, category, date, description),
    )
    conn.commit()
    exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return exp_id


def _create_other_user_expense():
    """Insert a second user with one expense; return that expense's id."""
    conn = db_module.get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Other User", "other@example.com", generate_password_hash("pass1234")),
    )
    conn.commit()
    other_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("other@example.com",)
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (other_id, 99.99, "Bills", "2026-05-01", "other-user-only"),
    )
    conn.commit()
    exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return exp_id


def _today():
    return str(datetime.date.today())


def _days_ago(n):
    return str(datetime.date.today() - datetime.timedelta(days=n))


# ------------------------------------------------------------------ #
# GET /expenses                                                        #
# ------------------------------------------------------------------ #

def test_expenses_requires_login(client):
    resp = client.get("/expenses")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_expenses_renders_200_when_authenticated(client):
    _login(client)
    resp = client.get("/expenses")
    assert resp.status_code == 200
    assert b"Your Expenses" in resp.data


def test_expenses_shows_own_expense(client):
    _login(client)
    _add_expense(description="my-personal-expense")
    resp = client.get("/expenses")
    assert b"my-personal-expense" in resp.data


def test_expenses_hides_other_users_expense(client):
    _login(client)
    _create_other_user_expense()
    resp = client.get("/expenses")
    assert b"other-user-only" not in resp.data


def test_expenses_empty_state_shown_with_no_expenses(client):
    _login(client)
    resp = client.get("/expenses")
    assert b"No expenses found" in resp.data


def test_expenses_total_displayed_in_overview(client):
    _login(client)
    _add_expense(amount=30.0, date="2026-05-01")
    _add_expense(amount=20.0, date="2026-05-02")
    resp = client.get("/expenses")
    assert b"50.00" in resp.data


def test_expenses_category_breakdown_displayed(client):
    _login(client)
    _add_expense(amount=40.0, category="Transport", date="2026-05-01")
    resp = client.get("/expenses")
    assert b"Transport" in resp.data
    assert b"40.00" in resp.data


def test_expenses_ordered_newest_first(client):
    _login(client)
    _add_expense(description="older-exp", date="2026-05-01")
    _add_expense(description="newer-exp", date="2026-05-10")
    resp = client.get("/expenses")
    newer_pos = resp.data.find(b"newer-exp")
    older_pos = resp.data.find(b"older-exp")
    assert newer_pos < older_pos


# ------------------------------------------------------------------ #
# GET /expenses — custom date filters                                  #
# ------------------------------------------------------------------ #

def test_expenses_filter_date_from(client):
    _login(client)
    _add_expense(description="new-exp", date="2026-06-01")
    _add_expense(description="old-exp", date="2026-01-01")
    resp = client.get("/expenses?date_from=2026-05-01")
    assert b"new-exp" in resp.data
    assert b"old-exp" not in resp.data


def test_expenses_filter_date_to(client):
    _login(client)
    _add_expense(description="new-exp", date="2026-06-01")
    _add_expense(description="old-exp", date="2026-01-01")
    resp = client.get("/expenses?date_to=2026-03-01")
    assert b"new-exp" not in resp.data
    assert b"old-exp" in resp.data


def test_expenses_filter_date_range(client):
    _login(client)
    _add_expense(description="in-range",  date="2026-05-15")
    _add_expense(description="too-early", date="2026-04-01")
    _add_expense(description="too-late",  date="2026-07-01")
    resp = client.get("/expenses?date_from=2026-05-01&date_to=2026-05-31")
    assert b"in-range"  in resp.data
    assert b"too-early" not in resp.data
    assert b"too-late"  not in resp.data


def test_expenses_filter_returns_all_when_no_params(client):
    _login(client)
    _add_expense(description="exp-a", date="2026-01-01")
    _add_expense(description="exp-b", date="2026-12-31")
    resp = client.get("/expenses")
    assert b"exp-a" in resp.data
    assert b"exp-b" in resp.data


# ------------------------------------------------------------------ #
# GET /expenses — preset filters                                       #
# ------------------------------------------------------------------ #

def test_expenses_preset_today(client):
    _login(client)
    _add_expense(description="today-exp",    date=_today())
    _add_expense(description="old-exp",      date=_days_ago(30))
    resp = client.get("/expenses?preset=today")
    assert b"today-exp" in resp.data
    assert b"old-exp"   not in resp.data


def test_expenses_preset_this_week(client):
    _login(client)
    today = datetime.date.today()
    before_week = today - datetime.timedelta(days=today.weekday() + 1)
    _add_expense(description="in-week-exp",  date=str(today))
    _add_expense(description="pre-week-exp", date=str(before_week))
    resp = client.get("/expenses?preset=this_week")
    assert b"in-week-exp"  in resp.data
    assert b"pre-week-exp" not in resp.data


def test_expenses_preset_last_week(client):
    _login(client)
    today = datetime.date.today()
    last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
    last_week_mid   = last_week_start + datetime.timedelta(days=3)
    _add_expense(description="last-week-exp", date=str(last_week_mid))
    _add_expense(description="today-exp",     date=str(today))
    resp = client.get("/expenses?preset=last_week")
    assert b"last-week-exp" in resp.data
    assert b"today-exp"     not in resp.data


def test_expenses_preset_this_month(client):
    _login(client)
    today = datetime.date.today()
    last_month_last = today.replace(day=1) - datetime.timedelta(days=1)
    _add_expense(description="this-month-exp", date=str(today))
    _add_expense(description="prev-month-exp", date=str(last_month_last))
    resp = client.get("/expenses?preset=this_month")
    assert b"this-month-exp" in resp.data
    assert b"prev-month-exp" not in resp.data


def test_expenses_preset_last_month(client):
    _login(client)
    today = datetime.date.today()
    last_month_end = today.replace(day=1) - datetime.timedelta(days=1)
    last_month_mid = last_month_end.replace(day=15)
    _add_expense(description="last-month-exp", date=str(last_month_mid))
    _add_expense(description="this-month-exp", date=str(today))
    resp = client.get("/expenses?preset=last_month")
    assert b"last-month-exp" in resp.data
    assert b"this-month-exp" not in resp.data


def test_expenses_preset_last_3_months(client):
    _login(client)
    _add_expense(description="recent-exp",   date=_days_ago(30))
    _add_expense(description="very-old-exp", date=_days_ago(100))
    resp = client.get("/expenses?preset=last_3_months")
    assert b"recent-exp"   in resp.data
    assert b"very-old-exp" not in resp.data


def test_expenses_unknown_preset_shows_all(client):
    _login(client)
    _add_expense(description="some-exp", date="2026-01-01")
    resp = client.get("/expenses?preset=nonexistent")
    assert b"some-exp" in resp.data


# ------------------------------------------------------------------ #
# POST /expenses/add                                                   #
# ------------------------------------------------------------------ #

def test_add_expense_requires_login(client):
    resp = client.post(ADD_URL, data={"amount": "50", "category": "Food", "date": "2026-05-01"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_add_expense_missing_amount(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "", "category": "Food", "date": "2026-05-01"})
    assert b"Amount, category, and date are required." in resp.data


def test_add_expense_missing_category(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "50", "category": "", "date": "2026-05-01"})
    assert b"Amount, category, and date are required." in resp.data


def test_add_expense_missing_date(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "50", "category": "Food", "date": ""})
    assert b"Amount, category, and date are required." in resp.data


def test_add_expense_amount_zero(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "0", "category": "Food", "date": "2026-05-01"})
    assert b"Amount must be a positive number." in resp.data


def test_add_expense_amount_negative(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "-10", "category": "Food", "date": "2026-05-01"})
    assert b"Amount must be a positive number." in resp.data


def test_add_expense_amount_not_a_number(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "abc", "category": "Food", "date": "2026-05-01"})
    assert b"Amount must be a positive number." in resp.data


def test_add_expense_invalid_category(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "50", "category": "Gambling", "date": "2026-05-01"})
    assert b"Invalid category selected." in resp.data


def test_add_expense_invalid_date_format(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "50", "category": "Food", "date": "31-12-2026"})
    assert b"Date must be in YYYY-MM-DD format." in resp.data


def test_add_expense_description_too_long(client):
    _login(client)
    resp = client.post(ADD_URL, data={
        "amount": "50", "category": "Food", "date": "2026-05-01",
        "description": "x" * 201,
    })
    assert b"Description must be 200 characters or fewer." in resp.data


def test_add_expense_success_redirects(client):
    _login(client)
    resp = client.post(ADD_URL, data={
        "amount": "42.50", "category": "Food",
        "date": "2026-05-10", "description": "Lunch",
    })
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/expenses"


def test_add_expense_success_persists_to_db(client):
    _login(client)
    client.post(ADD_URL, data={
        "amount": "42.50", "category": "Food",
        "date": "2026-05-10", "description": "Lunch",
    })
    conn = db_module.get_db()
    rows = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0]["amount"] == 42.50
    assert rows[0]["category"] == "Food"
    assert rows[0]["description"] == "Lunch"


def test_add_expense_description_is_optional(client):
    _login(client)
    resp = client.post(ADD_URL, data={"amount": "20", "category": "Transport", "date": "2026-05-01"})
    assert resp.status_code == 302
    conn = db_module.get_db()
    row = conn.execute("SELECT description FROM expenses").fetchone()
    conn.close()
    assert row["description"] is None


def test_add_expense_error_keeps_existing_list_visible(client):
    _login(client)
    _add_expense(description="pre-existing")
    resp = client.post(ADD_URL, data={"amount": "", "category": "Food", "date": "2026-05-01"})
    assert b"Amount, category, and date are required." in resp.data
    assert b"pre-existing" in resp.data


def test_add_expense_does_not_create_for_other_user(client):
    _login(client)
    _create_other_user_expense()
    client.post(ADD_URL, data={"amount": "10", "category": "Food", "date": "2026-05-01"})
    conn = db_module.get_db()
    test_user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("test@example.com",)
    ).fetchone()["id"]
    rows = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ?", (test_user_id,)
    ).fetchall()
    conn.close()
    assert len(rows) == 1


# ------------------------------------------------------------------ #
# POST /expenses/<id>/edit                                             #
# ------------------------------------------------------------------ #

def test_edit_expense_requires_login(client):
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/edit",
                       data={"amount": "60", "category": "Food", "date": "2026-05-01"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_edit_expense_success_redirects(client):
    _login(client)
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/edit",
                       data={"amount": "75", "category": "Transport", "date": "2026-05-15"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/expenses"


def test_edit_expense_success_updates_db(client):
    _login(client)
    exp_id = _add_expense(amount=50.0, category="Food", description="Original")
    client.post(f"/expenses/{exp_id}/edit", data={
        "amount": "75", "category": "Transport",
        "date": "2026-05-15", "description": "Updated",
    })
    conn = db_module.get_db()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (exp_id,)).fetchone()
    conn.close()
    assert row["amount"] == 75.0
    assert row["category"] == "Transport"
    assert row["description"] == "Updated"


def test_edit_expense_invalid_amount_zero(client):
    _login(client)
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/edit",
                       data={"amount": "0", "category": "Food", "date": "2026-05-01"})
    assert b"Amount must be a positive number." in resp.data


def test_edit_expense_invalid_amount_negative(client):
    _login(client)
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/edit",
                       data={"amount": "-5", "category": "Food", "date": "2026-05-01"})
    assert b"Amount must be a positive number." in resp.data


def test_edit_expense_invalid_category(client):
    _login(client)
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/edit",
                       data={"amount": "50", "category": "Unicorn", "date": "2026-05-01"})
    assert b"Invalid category selected." in resp.data


def test_edit_expense_invalid_date_format(client):
    _login(client)
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/edit",
                       data={"amount": "50", "category": "Food", "date": "2026/05/01"})
    assert b"Date must be in YYYY-MM-DD format." in resp.data


def test_edit_expense_description_too_long(client):
    _login(client)
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/edit", data={
        "amount": "50", "category": "Food", "date": "2026-05-01",
        "description": "y" * 201,
    })
    assert b"Description must be 200 characters or fewer." in resp.data


def test_edit_expense_other_users_expense_redirects(client):
    _login(client)
    other_exp_id = _create_other_user_expense()
    resp = client.post(f"/expenses/{other_exp_id}/edit",
                       data={"amount": "10", "category": "Food", "date": "2026-05-01"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/expenses"


def test_edit_expense_other_users_expense_not_modified(client):
    _login(client)
    other_exp_id = _create_other_user_expense()
    client.post(f"/expenses/{other_exp_id}/edit",
                data={"amount": "1.00", "category": "Food", "date": "2026-05-01"})
    conn = db_module.get_db()
    row = conn.execute("SELECT amount FROM expenses WHERE id = ?", (other_exp_id,)).fetchone()
    conn.close()
    assert row["amount"] == 99.99


def test_edit_nonexistent_expense_redirects(client):
    _login(client)
    resp = client.post("/expenses/99999/edit",
                       data={"amount": "10", "category": "Food", "date": "2026-05-01"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/expenses"


def test_edit_expense_error_keeps_list_visible(client):
    _login(client)
    exp_id = _add_expense(description="editable-expense")
    resp = client.post(f"/expenses/{exp_id}/edit",
                       data={"amount": "0", "category": "Food", "date": "2026-05-01"})
    assert b"Amount must be a positive number." in resp.data
    assert b"editable-expense" in resp.data


# ------------------------------------------------------------------ #
# POST /expenses/<id>/delete                                           #
# ------------------------------------------------------------------ #

def test_delete_expense_requires_login(client):
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_delete_expense_success_redirects(client):
    _login(client)
    exp_id = _add_expense()
    resp = client.post(f"/expenses/{exp_id}/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/expenses"


def test_delete_expense_success_removes_from_db(client):
    _login(client)
    exp_id = _add_expense()
    client.post(f"/expenses/{exp_id}/delete")
    conn = db_module.get_db()
    row = conn.execute("SELECT id FROM expenses WHERE id = ?", (exp_id,)).fetchone()
    conn.close()
    assert row is None


def test_delete_expense_other_users_expense_redirects(client):
    _login(client)
    other_exp_id = _create_other_user_expense()
    resp = client.post(f"/expenses/{other_exp_id}/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/expenses"


def test_delete_expense_other_users_expense_not_removed(client):
    _login(client)
    other_exp_id = _create_other_user_expense()
    client.post(f"/expenses/{other_exp_id}/delete")
    conn = db_module.get_db()
    row = conn.execute("SELECT id FROM expenses WHERE id = ?", (other_exp_id,)).fetchone()
    conn.close()
    assert row is not None


def test_delete_nonexistent_expense_redirects(client):
    _login(client)
    resp = client.post("/expenses/99999/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/expenses"
