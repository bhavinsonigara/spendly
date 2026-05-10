## 1. Overview

Implement three UX improvements: **Spending Chart**, **Search by Description**, and **Sort Controls**.

All three extend the existing `GET /expenses` route and `expenses.html` template. No new DB tables are required.

---

## 2. Depends on

- Step 5 — Expenses dashboard complete (`GET /expenses`, `expenses.html` working)
- Spec 06 — Budget card in place (the filter section already exists to add controls into)

---

## 3. Routes

### `GET /expenses` (extended further)

New query params added alongside existing `preset`, `date_from`, `date_to`:

| Param | Default | Description |
|-------|---------|-------------|
| `q` | `""` | Search term — matches description or category (case-insensitive LIKE) |
| `sort` | `"date_desc"` | Sort order — one of `date_desc`, `date_asc`, `amount_desc`, `amount_asc` |

Pass `q` and `sort` back to the template so controls remain populated between requests.

No new routes are added for this spec — all changes are to the existing `GET /expenses` handler.

---

## 4. Database Schema

No new tables or columns.

---

## 5. Validation Rules

### Search (`q`)

- Trim whitespace; empty string means no filter
- Max 100 characters (silently truncate on server, no error shown)

### Sort (`sort`)

- Must be one of the keys in `SORT_OPTIONS`; default to `"date_desc"` for any unrecognised value
- Never pass the sort string directly into SQL — look it up in the whitelist dict

---

## 6. Backend Changes (`app.py`)

### Add `SORT_OPTIONS` constant (module level)

```python
SORT_OPTIONS = {
    "date_desc":   "date DESC, id DESC",
    "date_asc":    "date ASC,  id ASC",
    "amount_desc": "amount DESC",
    "amount_asc":  "amount ASC",
}
```

### Extend `GET /expenses` handler

Read new params:

```python
q    = request.args.get("q", "").strip()[:100]
sort = request.args.get("sort", "date_desc")
order_clause = SORT_OPTIONS.get(sort, SORT_OPTIONS["date_desc"])
```

Extend query building:

```python
if q:
    query += " AND (description LIKE ? OR category LIKE ?)"
    params += [f"%{q}%", f"%{q}%"]
query += f" ORDER BY {order_clause}"
```

Pass new values to template:

```python
return render_template(
    "expenses.html",
    ...,
    q=q,
    sort=sort,
    sort_options=SORT_OPTIONS,
)
```

### Extend `_expenses_context()` helper

Add `q=""` and `sort="date_desc"` keys to the returned dict so add/edit error re-renders also pass these to the template.

---

## 7. Template — `expenses.html` changes

### A. Chart (inside the existing summary card)

Add Chart.js CDN before `</body>` (or in a `{% block scripts %}` extension of `base.html`):

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
```

Add canvas to the summary card, alongside the existing category breakdown:

```html
<div class="chart-wrap">
  <canvas id="categoryChart" width="220" height="220"></canvas>
</div>
```

Inline script block at the bottom of `expenses.html`:

```html
<script>
(function () {
  var ctx = document.getElementById("categoryChart");
  if (!ctx) return;
  var data = {{ by_category | tojson }};
  var labels = Object.keys(data);
  var values = Object.values(data);
  var colors = ["#1a472a","#c17f24","#2980b9","#8e44ad","#e67e22","#27ae60","#7f8c8d"];
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderWidth: 2 }]
    },
    options: { plugins: { legend: { position: "bottom" } }, cutout: "60%" }
  });
})();
</script>
```

Only render the canvas block `{% if by_category %}` to avoid an empty chart.

### B. Search input (filter section)

Add inside the existing filter form or as a sibling form:

```html
<form method="GET" action="/expenses" class="search-row">
  <input type="text" name="q" value="{{ q }}" placeholder="Search description or category…"
         class="form-input search-input" maxlength="100">
  <!-- preserve other active filters -->
  <input type="hidden" name="preset" value="{{ preset }}">
  <input type="hidden" name="date_from" value="{{ date_from }}">
  <input type="hidden" name="date_to" value="{{ date_to }}">
  <input type="hidden" name="sort" value="{{ sort }}">
  <button type="submit" class="btn-ghost">Search</button>
  {% if q %}<a href="/expenses" class="btn-ghost">Clear</a>{% endif %}
</form>
```

### C. Sort dropdown (filter section)

```html
<div class="sort-row">
  <label for="sort-select" class="form-label">Sort by</label>
  <select id="sort-select" name="sort" class="form-input sort-select"
          onchange="this.form.submit()">
    <option value="date_desc"   {% if sort == "date_desc"   %}selected{% endif %}>Date (newest)</option>
    <option value="date_asc"    {% if sort == "date_asc"    %}selected{% endif %}>Date (oldest)</option>
    <option value="amount_desc" {% if sort == "amount_desc" %}selected{% endif %}>Amount (high–low)</option>
    <option value="amount_asc"  {% if sort == "amount_asc"  %}selected{% endif %}>Amount (low–high)</option>
  </select>
</div>
```

The sort select must be inside a `<form method="GET" action="/expenses">` that also carries `preset`, `date_from`, `date_to`, and `q` as hidden inputs.

---

## 8. CSS additions (`static/css/style.css`)

```css
.chart-wrap     { display: flex; justify-content: center; margin-top: 1.25rem; }
.search-row     { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.75rem; }
.search-input   { flex: 1; }
.sort-row       { display: flex; align-items: center; gap: 0.5rem; }
.sort-select    { width: auto; }
```

---

## 9. Files to Change

- `app.py` — add `SORT_OPTIONS`; extend `GET /expenses` with `q` and `sort` params; update `_expenses_context()`
- `templates/expenses.html` — add chart canvas + inline script, search form, sort dropdown
- `static/css/style.css` — add chart, search, and sort styles

---

## 10. Files to Create

- None

---

## 11. Dependencies

- Chart.js via CDN (`https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js`) — no pip install
- No new Python packages

---

## 12. Rules for Implementation

- Never interpolate `sort` directly into SQL — always look up via `SORT_OPTIONS` whitelist
- LIKE queries must use parameterized `?` placeholders with `%value%` strings, never f-strings in SQL
- Chart renders only when `by_category` is non-empty
- `q` and `sort` must be preserved across filter preset/date-range submissions (hidden inputs)
- `_expenses_context()` must also return `q` and `sort` so error re-renders don't lose them

---

## 13. Definition of Done

- [ ] `SORT_OPTIONS` dict defined at module level in `app.py`
- [ ] `GET /expenses` reads `q` and `sort` query params
- [ ] Search filters expenses by description or category (case-insensitive)
- [ ] Sort changes the ORDER BY correctly for all four options
- [ ] Unknown sort value falls back to `date_desc`
- [ ] Chart renders as a doughnut on the summary card when there are expenses
- [ ] Chart does not render (no empty canvas) when there are no expenses
- [ ] Search input preserves value between requests
- [ ] Sort dropdown shows the active selection between requests
- [ ] `q` and `sort` are preserved when switching date presets
- [ ] All SQL uses parameterized queries (no sort string injection)
