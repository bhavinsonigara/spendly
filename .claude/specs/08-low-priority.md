## 1. Overview

Implement two lower-priority quality-of-life features: **Pagination** and **Delete Account**.

Pagination prevents the expense list from becoming unwieldy when a user has many entries. Delete Account gives users control over their data, completing the account lifecycle.

---

## 2. Depends on

- Step 1 — `database/db.py` complete
- Step 3 — Login/logout complete (`session` management working)
- Step 4 — Profile page complete (delete account UI lives there)
- Step 5 — Expenses dashboard complete (`GET /expenses` working)

---

## 3. Routes

### A. Pagination — `GET /expenses` (extended)

New query param:

| Param | Default | Description |
|-------|---------|-------------|
| `page` | `1` | Current page number (integer, min 1) |

`PAGE_SIZE = 20` defined as a module-level constant in `app.py`.

Totals (`total` spend and `by_category`) are always computed from the **full filtered result set**, not the current page slice, so the summary bar remains accurate.

### B. Delete Account — `POST /profile/delete-account`

- Requires active session
- Accepts form field: `password` (current password for confirmation)
- Deletes all the user's expenses, then the user row
- Clears the session
- Redirects to `/?deleted=1`

### `GET /` (extended slightly)

- If `request.args.get("deleted") == "1"` → pass `account_deleted=True` to `landing.html` so it can show a one-time banner

---

## 4. Database Schema

No new tables or columns.

---

## 5. Validation Rules

### Pagination (`GET /expenses`)

- `page` must be a positive integer; coerce: `max(1, int(request.args.get("page", 1)))` with a try/except defaulting to 1 on non-integer input
- If `page` exceeds `total_pages`, clamp to `total_pages` (avoids empty pages)

### Delete account (`POST /profile/delete-account`)

| Field | Rule |
|-------|------|
| password | Required; must match the stored hash for `session["user_id"]` |

- If password is missing → re-render `profile.html` with `delete_error="Password is required."`
- If password is wrong → re-render `profile.html` with `delete_error="Incorrect password."`

---

## 6. Database Operations

### Pagination — count total matching rows

```sql
SELECT COUNT(*) FROM expenses WHERE user_id = ? [+ same date/search filters]
```

Run this before the paged query so `total_pages = ceil(count / PAGE_SIZE)`.

### Pagination — fetch one page

```sql
SELECT id, amount, category, date, description
FROM expenses
WHERE user_id = ? [+ filters]
ORDER BY <sort_clause>
LIMIT ? OFFSET ?
```

`OFFSET = (page - 1) * PAGE_SIZE`

### Totals — compute from full result (not paged)

Run a second query without LIMIT/OFFSET to get all rows for sum/category breakdown, OR compute them from the COUNT + a separate SUM query per category. Simpler: fetch all rows for totals, fetch paged rows for the list.

```sql
SELECT category, SUM(amount) as subtotal FROM expenses
WHERE user_id = ? [+ filters]
GROUP BY category
```

### Delete account

```sql
DELETE FROM expenses WHERE user_id = ?   -- remove all expenses first
DELETE FROM users WHERE id = ?           -- then remove the user
```

Run both inside the same `db = get_db(); try: ... db.commit(); finally: db.close()` block.

---

## 7. Error Messages

### Pagination

No error messages — invalid `page` values are silently clamped.

### Delete account

| Condition | Variable | Message |
|-----------|----------|---------|
| Password field empty | `delete_error` | "Password is required." |
| Password incorrect | `delete_error` | "Incorrect password." |

---

## 8. Template Changes

### A. `expenses.html` — pagination nav

Add below the expense list, inside the expenses card:

```html
{% if total_pages > 1 %}
<nav class="pagination">
  {% if has_prev %}
    <a href="?page={{ page - 1 }}&preset={{ preset }}&date_from={{ date_from }}&date_to={{ date_to }}&q={{ q }}&sort={{ sort }}"
       class="btn-ghost page-btn">← Prev</a>
  {% endif %}
  <span class="page-info">Page {{ page }} of {{ total_pages }}</span>
  {% if has_next %}
    <a href="?page={{ page + 1 }}&preset={{ preset }}&date_from={{ date_from }}&date_to={{ date_to }}&q={{ q }}&sort={{ sort }}"
       class="btn-ghost page-btn">Next →</a>
  {% endif %}
</nav>
{% endif %}
```

### B. `profile.html` — delete account section

Add as the last `.auth-card` on the page:

```html
<section class="auth-card danger-zone">
  <h2>Delete Account</h2>
  <p class="danger-warning">This permanently deletes your account and all expenses. This cannot be undone.</p>
  {% if delete_error %}<div class="auth-error">{{ delete_error }}</div>{% endif %}
  <form method="POST" action="/profile/delete-account">
    <div class="form-group">
      <label class="form-label" for="del-password">Confirm your password</label>
      <input class="form-input" type="password" id="del-password" name="password"
             placeholder="Enter current password" required>
    </div>
    <button type="submit" class="btn-danger-solid">Delete My Account</button>
  </form>
</section>
```

### C. `landing.html` — deleted account banner

Add at the top of `<main>`, before the hero:

```html
{% if account_deleted %}
<div class="deleted-banner">
  Your account has been deleted. Sorry to see you go.
</div>
{% endif %}
```

---

## 9. CSS additions (`static/css/style.css`)

```css
/* Pagination */
.pagination      { display: flex; align-items: center; gap: 0.75rem; justify-content: center; padding-top: 1rem; border-top: 1px solid var(--border); margin-top: 0.5rem; }
.page-btn        { font-size: 0.85rem; padding: 0.4rem 0.9rem; }
.page-info       { font-size: 0.85rem; color: var(--ink-muted); }

/* Delete account */
.danger-zone     { border-color: var(--danger); }
.danger-warning  { font-size: 0.875rem; color: var(--ink-muted); margin-bottom: 1rem; }
.btn-danger-solid { display: block; width: 100%; padding: 0.65rem 1.5rem; background: var(--danger); color: #fff; border: none; border-radius: var(--radius-sm); font-family: var(--font-body); font-size: 0.9rem; cursor: pointer; margin-top: 0.5rem; transition: opacity 0.2s; }
.btn-danger-solid:hover { opacity: 0.85; }

/* Deleted account banner */
.deleted-banner  { background: var(--accent-light); color: var(--accent); border: 1px solid var(--accent); border-radius: var(--radius-sm); padding: 0.75rem 1rem; text-align: center; font-size: 0.9rem; max-width: var(--max-width); margin: 1.5rem auto 0; }
```

---

## 10. Files to Change

- `app.py` — add `PAGE_SIZE`; extend `GET /expenses` with pagination; add `POST /profile/delete-account`; extend `GET /` to pass `account_deleted`
- `templates/expenses.html` — add pagination nav
- `templates/profile.html` — add delete account card
- `templates/landing.html` — add deleted account banner
- `static/css/style.css` — add pagination, danger zone, and banner styles

---

## 11. Files to Create

- None

---

## 12. Dependencies

- `math.ceil` (stdlib) for total page calculation
- No new pip packages

---

## 13. Rules for Implementation

- Totals and `by_category` must always reflect the **full filtered set**, not the current page
- `page` param must be clamped: never below 1, never above `total_pages`
- Delete account must delete expenses **before** the user row (foreign key constraint)
- Both deletes must be in one transaction (single `db.commit()`)
- Auth guard at top of `POST /profile/delete-account`
- `GET /` must not break if `?deleted=1` is absent (default `account_deleted=False`)
- All SQL uses parameterized queries

---

## 14. Definition of Done

- [ ] `PAGE_SIZE = 20` defined at module level
- [ ] `GET /expenses` reads `page` param; clamps to valid range
- [ ] Expense list shows only `PAGE_SIZE` rows per page
- [ ] Totals and `by_category` reflect the full filtered set (not the page slice)
- [ ] Pagination nav renders only when `total_pages > 1`
- [ ] Prev/Next links carry all active filter params
- [ ] `POST /profile/delete-account` is auth-guarded
- [ ] Wrong password returns correct `delete_error`
- [ ] Successful deletion removes all expenses then the user row
- [ ] Session is cleared after deletion
- [ ] Redirects to `/?deleted=1` after deletion
- [ ] Landing page shows the deleted banner when `?deleted=1` is present
- [ ] All SQL uses parameterized queries
