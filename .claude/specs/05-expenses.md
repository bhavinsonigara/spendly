## 1. Overview

Implement the expenses dashboard (`GET /expenses`) and expense management routes: add (`POST /expenses/add`), edit (`POST /expenses/<id>/edit`), and delete (`POST /expenses/<id>/delete`).

The dashboard is the main authenticated view of the app. It lists all expenses belonging to the logged-in user, shows a running total and a per-category breakdown, and exposes inline forms to add, edit, and delete entries. All data is scoped strictly to the session user — no user can read or modify another user's expenses.

---

## 2. Depends on

- Step 1 — `database/db.py` must be complete (`get_db()` working, `expenses` table created)
- Step 2 — Registration must be complete so real user accounts exist
- Step 3 — Login/logout must be complete so `session["user_id"]` is reliably set

---

## 3. Routes

### `GET /expenses`

- Requires an active session
- Fetches all expenses for `session["user_id"]`, ordered by `date DESC, id DESC`
- Computes total spend and a per-category subtotal dict
- Renders `expenses.html` with `expenses`, `total`, and `by_category`

### `POST /expenses/add`

- Requires an active session
- Accepts form fields: `amount`, `category`, `date`, `description` (optional)
- On success → redirect to `/expenses` (PRG pattern)
- On failure → re-render `expenses.html` with an `add_error` variable (and repopulate the full expense list so the page is usable)

### `POST /expenses/<int:id>/edit`

- Requires an active session
- Accepts form fields: `amount`, `category`, `date`, `description` (optional)
- Must verify the expense belongs to `session["user_id"]` before updating
- On success → redirect to `/expenses`
- On failure → re-render `expenses.html` with an `edit_error` and `edit_id` so the correct inline form stays open

### `POST /expenses/<int:id>/delete`

- Requires an active session
- Must verify the expense belongs to `session["user_id"]` before deleting
- On success → redirect to `/expenses`
- Attempting to delete a non-existent or foreign expense → redirect to `/expenses` (silent no-op)

---

## 4. Auth Guard

Every handler must redirect unauthenticated users:

- If `session.get("user_id")` is falsy → `redirect(url_for("login"))`
- Check at the very top of every handler before any DB access

---

## 5. Validation Rules

### Add expense (`POST /expenses/add`)

| Field | Rule |
| --- | --- |
| amount | Required; must be a positive number; max 2 decimal places accepted |
| category | Required; must be one of the allowed categories (see §8) |
| date | Required; must be a valid `YYYY-MM-DD` string |
| description | Optional; max 200 characters if provided |

### Edit expense (`POST /expenses/<id>/edit`)

Same rules as add. Additionally:

- Expense `id` must exist and belong to `session["user_id"]`; if not → redirect to `/expenses`

### Delete expense (`POST /expenses/<id>/delete`)

- Expense `id` must exist and belong to `session["user_id"]`; otherwise → redirect (no error shown)

---

## 6. Allowed Categories

```python
CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
```

Define this constant at module level in `app.py` and pass it to templates as `categories`.

---

## 7. Database Operations

### Fetch all expenses for the logged-in user

```sql
SELECT id, amount, category, date, description
FROM expenses
WHERE user_id = ?
ORDER BY date DESC, id DESC
```

### Insert a new expense

```sql
INSERT INTO expenses (user_id, amount, category, date, description)
VALUES (?, ?, ?, ?, ?)
```

### Update an existing expense (ownership check first)

```sql
SELECT id FROM expenses WHERE id = ? AND user_id = ?   -- ownership check
UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?
```

### Delete an expense (ownership check implicit in WHERE)

```sql
DELETE FROM expenses WHERE id = ? AND user_id = ?
```

Use parameterized queries only — never string-format SQL.

---

## 8. Summary Calculations (Python, not SQL)

Compute in the route handler after fetching the expense list:

```python
total = sum(e["amount"] for e in expenses)
by_category = {}
for e in expenses:
    by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]
```

Pass `total` and `by_category` to the template.

---

## 9. Error Messages

### Add expense errors

| Condition | Variable | Message |
| --- | --- | --- |
| Any required field is empty | `add_error` | "Amount, category, and date are required." |
| Amount is not a valid positive number | `add_error` | "Amount must be a positive number." |
| Category not in allowed list | `add_error` | "Invalid category selected." |
| Date is not valid YYYY-MM-DD | `add_error` | "Date must be in YYYY-MM-DD format." |
| Description exceeds 200 chars | `add_error` | "Description must be 200 characters or fewer." |

### Edit expense errors

Same messages as add, using `edit_error`. Also pass `edit_id = id` so the template can keep the correct edit form open.

---

## 10. Template — `expenses.html`

Extends `base.html`. Uses only existing CSS classes from `style.css`.

### Layout

```
<main class="expenses-page">

  <!-- Summary bar -->
  <section class="card summary-bar">
    <h2>Total Spent: £{{ "%.2f"|format(total) }}</h2>
    <ul class="category-breakdown">
      {% for cat, subtotal in by_category.items() %}
        <li>{{ cat }}: £{{ "%.2f"|format(subtotal) }}</li>
      {% endfor %}
    </ul>
  </section>

  <!-- Add expense form -->
  <section class="card">
    <h2>Add Expense</h2>
    {% if add_error %}<p class="auth-error">{{ add_error }}</p>{% endif %}
    <form method="POST" action="/expenses/add">
      <input type="number" name="amount" step="0.01" min="0.01" placeholder="Amount" required>
      <select name="category">
        {% for cat in categories %}
          <option value="{{ cat }}">{{ cat }}</option>
        {% endfor %}
      </select>
      <input type="date" name="date" required>
      <input type="text" name="description" placeholder="Description (optional)" maxlength="200">
      <button type="submit" class="btn-submit">Add</button>
    </form>
  </section>

  <!-- Expense list -->
  <section class="card">
    <h2>Your Expenses</h2>
    {% if not expenses %}
      <p>No expenses yet. Add one above.</p>
    {% else %}
      <ul class="expense-list">
        {% for e in expenses %}
          <li class="expense-item">
            <span class="expense-date">{{ e.date }}</span>
            <span class="expense-category">{{ e.category }}</span>
            <span class="expense-desc">{{ e.description or "—" }}</span>
            <span class="expense-amount">£{{ "%.2f"|format(e.amount) }}</span>

            <!-- Edit form (shown inline) -->
            <form method="POST" action="/expenses/{{ e.id }}/edit" class="edit-form">
              {% if edit_error and edit_id == e.id %}
                <p class="auth-error">{{ edit_error }}</p>
              {% endif %}
              <input type="number" name="amount" step="0.01" min="0.01" value="{{ e.amount }}" required>
              <select name="category">
                {% for cat in categories %}
                  <option value="{{ cat }}" {% if cat == e.category %}selected{% endif %}>{{ cat }}</option>
                {% endfor %}
              </select>
              <input type="date" name="date" value="{{ e.date }}" required>
              <input type="text" name="description" value="{{ e.description or '' }}" maxlength="200">
              <button type="submit" class="btn-submit">Save</button>
            </form>

            <!-- Delete form -->
            <form method="POST" action="/expenses/{{ e.id }}/delete" class="delete-form">
              <button type="submit" class="btn-ghost">Delete</button>
            </form>
          </li>
        {% endfor %}
      </ul>
    {% endif %}
  </section>

</main>
```

- Do not add new global CSS classes — use `.card`, `.btn-submit`, `.btn-ghost`, `.auth-error` from `style.css`
- Add layout-only rules scoped to `.expenses-page` if needed for the expense list grid; keep them minimal

---

## 11. Files to Change

- `app.py` — replace the `GET /expenses`, `POST /expenses/add`, `POST /expenses/<id>/edit`, and `POST /expenses/<id>/delete` stubs; add the `CATEGORIES` constant

---

## 12. Files to Create

- `templates/expenses.html` — expenses dashboard template extending `base.html`

---

## 13. Dependencies

- No new pip packages
- Use:
  - `flask`: `request`, `redirect`, `url_for`, `session` (already imported)
  - `database.db`: `get_db` (already imported)

---

## 14. Rules for Implementation

- Use parameterized queries only — never string-format SQL
- Validate all fields before opening a database connection
- Close the database connection after every query (use `try/finally`)
- Apply the auth guard at the top of every handler before any other logic
- Follow the PRG pattern on all successful POST operations
- Always include `AND user_id = ?` in UPDATE and DELETE queries — never rely on id alone
- Pass `categories` to every `render_template` call so the add and edit dropdowns always populate
- On `add_error` or `edit_error`, re-fetch the full expense list before re-rendering

---

## 15. Expected Behavior

- Visiting `/expenses` while logged out redirects to `/login`
- Visiting `/expenses` while logged in shows the expense list, total, and category breakdown
- An account with no expenses shows the empty-state message
- Submitting a valid add form inserts the expense and redirects to `/expenses`
- Submitting an invalid add form re-renders the page with `add_error` and the full list intact
- Submitting a valid edit form updates the expense and redirects to `/expenses`
- Submitting an invalid edit form re-renders the page with `edit_error` and `edit_id` set
- Submitting a delete form removes the expense and redirects to `/expenses`
- A user cannot view, edit, or delete another user's expenses

---

## 16. Definition of Done

- [ ] `GET /expenses` redirects unauthenticated users to `/login`
- [ ] `GET /expenses` renders `expenses.html` with the logged-in user's expenses only
- [ ] Total spend and per-category breakdown are computed and displayed correctly
- [ ] Empty-state message is shown when there are no expenses
- [ ] `POST /expenses/add` validates all required fields before any DB operation
- [ ] Successful add inserts the expense and redirects to `/expenses`
- [ ] Failed add re-renders the page with `add_error` and a populated expense list
- [ ] `POST /expenses/<id>/edit` validates all required fields before any DB operation
- [ ] Successful edit updates the expense and redirects to `/expenses`
- [ ] Failed edit re-renders the page with `edit_error` and `edit_id` set correctly
- [ ] `POST /expenses/<id>/delete` removes the expense and redirects to `/expenses`
- [ ] All UPDATE and DELETE queries include `AND user_id = ?` to enforce ownership
- [ ] All SQL uses parameterized queries
- [ ] No new pip packages introduced
