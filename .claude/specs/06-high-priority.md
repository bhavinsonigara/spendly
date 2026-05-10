## 1. Overview

Implement two high-value features: **Monthly Budget Limits** and **CSV Export**.

Budget limits let users set a spending cap per category for the current month and see a live progress bar on the expenses dashboard. CSV export lets users download their filtered expense list as a spreadsheet with zero new dependencies.

---

## 2. Depends on

- Step 1 — `database/db.py` complete (`get_db`, `init_db` working)
- Step 5 — Expenses dashboard complete (`GET /expenses` with date filtering working)

---

## 3. Routes

### A. Budget Limits

#### `POST /budgets/set`

- Requires active session
- Accepts form fields: `category`, `amount`
- Upserts a row in the `budgets` table for the current month (`YYYY-MM`)
- On success → redirect to `/expenses`
- On failure → redirect to `/expenses` with `?budget_error=<message>`

#### `GET /expenses` (extended)

- Already exists — extend it to also:
  - Fetch all budgets for `session["user_id"]` for the current month
  - Compute `spent` per category from the current month's expenses (regardless of active date filter)
  - Pass `budgets` dict `{category: {amount, spent, pct}}` to the template

---

### B. CSV Export

#### `GET /expenses/export`

- Requires active session
- Accepts same query params as `GET /expenses`: `preset`, `date_from`, `date_to`
- Fetches matching expenses for `session["user_id"]`
- Returns a `text/csv` response with `Content-Disposition: attachment; filename=expenses.csv`
- Columns: `Date`, `Category`, `Description`, `Amount`

---

## 4. Database Schema

### New table: `budgets`

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Foreign key → users.id, not null |
| category | TEXT | Not null |
| amount | REAL | Not null |
| month | TEXT | Not null (YYYY-MM format) |

Unique constraint: `(user_id, category, month)` — only one budget per category per user per month.

Add to `init_db()` in `database/db.py` using `CREATE TABLE IF NOT EXISTS`.

---

## 5. Validation Rules

### Set budget (`POST /budgets/set`)

| Field | Rule |
|-------|------|
| category | Required; must be one of the CATEGORIES list |
| amount | Required; must be a positive number |

- If validation fails → redirect to `/expenses?budget_error=<message>`
- Month is always the current calendar month (computed server-side, not from form)

### CSV export (`GET /expenses/export`)

- No extra validation beyond auth guard
- Invalid date params are silently ignored (same as `GET /expenses`)

---

## 6. Database Operations

### Upsert a budget

```sql
INSERT INTO budgets (user_id, category, amount, month)
VALUES (?, ?, ?, ?)
ON CONFLICT(user_id, category, month) DO UPDATE SET amount = excluded.amount
```

### Fetch budgets for current month

```sql
SELECT category, amount FROM budgets
WHERE user_id = ? AND month = ?
```

Pass current month as `datetime.date.today().strftime("%Y-%m")`.

### Fetch current-month spend per category (for budget progress)

```sql
SELECT category, SUM(amount) as spent
FROM expenses
WHERE user_id = ? AND date >= ? AND date <= ?
GROUP BY category
```

Use first and last day of current month as bounds.

### Fetch expenses for CSV

Reuse the same filtered query as `GET /expenses` (same `preset`/`date_from`/`date_to` logic).

---

## 7. Error Messages

| Condition | Behavior |
|-----------|----------|
| category missing or invalid | Redirect `/expenses?budget_error=Invalid category.` |
| amount missing or not positive | Redirect `/expenses?budget_error=Amount must be a positive number.` |

Show `budget_error` in a `.auth-error` div in the budgets card on the expenses page.

---

## 8. Template — `expenses.html` changes

### Budget card (new section, after summary bar)

```
<section class="auth-card">
  <h2>Monthly Budgets</h2>
  {% if budget_error %}<div class="auth-error">{{ budget_error }}</div>{% endif %}

  <!-- Set budget form -->
  <form method="POST" action="/budgets/set" class="add-form-grid">
    <select name="category" class="form-input">
      {% for cat in categories %}
        <option value="{{ cat }}">{{ cat }}</option>
      {% endfor %}
    </select>
    <input type="number" name="amount" step="0.01" min="0.01"
           placeholder="Monthly limit" class="form-input">
    <button type="submit" class="btn-submit">Set</button>
  </form>

  <!-- Budget progress rows -->
  {% if budgets %}
    <ul class="budget-list">
      {% for cat, b in budgets.items() %}
        <li class="budget-row {% if b.pct >= 100 %}budget-over{% endif %}">
          <span class="budget-label">{{ cat }}</span>
          <div class="budget-bar">
            <div class="budget-bar-fill" style="width: {{ [b.pct, 100]|min }}%"></div>
          </div>
          <span class="budget-amounts">
            £{{ "%.2f"|format(b.spent) }} / £{{ "%.2f"|format(b.amount) }}
          </span>
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p class="budget-empty">No budgets set for this month.</p>
  {% endif %}
</section>
```

### CSV export button

Add to the filter section:

```html
<a href="/expenses/export?preset={{ preset }}&date_from={{ date_from }}&date_to={{ date_to }}"
   class="btn-ghost export-btn">Export CSV</a>
```

---

## 9. CSS additions (`static/css/style.css`)

Scoped to `.expenses-page`:

```css
.budget-list   { list-style: none; padding: 0; margin-top: 1rem; display: flex; flex-direction: column; gap: 0.6rem; }
.budget-row    { display: grid; grid-template-columns: 110px 1fr auto; gap: 0.75rem; align-items: center; }
.budget-label  { font-size: 0.85rem; font-weight: 500; }
.budget-bar    { height: 8px; background: var(--border); border-radius: 999px; overflow: hidden; }
.budget-bar-fill { height: 100%; background: var(--accent); border-radius: 999px; transition: width 0.3s; }
.budget-over .budget-bar-fill { background: var(--danger); }
.budget-over .budget-label    { color: var(--danger); }
.budget-amounts { font-size: 0.8rem; color: var(--ink-muted); white-space: nowrap; }
.budget-empty   { font-size: 0.875rem; color: var(--ink-muted); margin-top: 0.75rem; }
.export-btn     { font-size: 0.85rem; padding: 0.5rem 1rem; }
```

---

## 10. Files to Change

- `database/db.py` — add `budgets` table to `init_db()`
- `app.py` — add `POST /budgets/set`, `GET /expenses/export`; extend `GET /expenses` to load budgets
- `templates/expenses.html` — add budget card and CSV export button
- `static/css/style.css` — add budget bar and export button styles

---

## 11. Files to Create

- None

---

## 12. Dependencies

- No new pip packages
- Use: `csv`, `io` (stdlib); `datetime` (already imported)

---

## 13. Rules for Implementation

- Use parameterized queries only — never string-format SQL
- Budget month is always computed server-side: `datetime.date.today().strftime("%Y-%m")`
- Use `INSERT OR REPLACE` / `ON CONFLICT DO UPDATE` for upsert
- CSV response must set correct headers: `Content-Type: text/csv`, `Content-Disposition: attachment; filename=expenses.csv`
- Close all DB connections in `try/finally`
- Auth guard at top of every new route

---

## 14. Definition of Done

- [ ] `budgets` table created on `init_db()` with correct schema and unique constraint
- [ ] `POST /budgets/set` upserts correctly for the current month
- [ ] `GET /expenses` passes `budgets` dict with `amount`, `spent`, `pct` per category
- [ ] Budget card renders on expenses page with progress bars
- [ ] Over-budget categories shown in red
- [ ] Budget form validation returns correct error messages
- [ ] `GET /expenses/export` returns a downloadable CSV with correct columns
- [ ] CSV export respects the same date filters as the dashboard
- [ ] CSV is scoped to the logged-in user only
- [ ] All SQL uses parameterized queries
