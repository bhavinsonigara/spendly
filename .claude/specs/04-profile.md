## 1. Overview

Implement the user profile page by wiring the `GET /profile` route in `app.py` and creating the `profile.html` template.

The profile page is a protected page that shows the logged-in user's account details (name, email, join date) and provides two independent inline forms: one to update their display name and one to change their password.

---

## 2. Depends on

- Step 1 — `database/db.py` must be complete (`get_db()` working, `users` table created)
- Step 2 — Registration must be complete so that real user accounts exist
- Step 3 — Login/logout must be complete so that `session["user_id"]` is reliably set

---

## 3. Routes

### `GET /profile`

- Requires an active session (`session["user_id"]` must exist)
- Fetches the current user row from the `users` table by `session["user_id"]`
- Renders `profile.html` with a `user` variable (the DB row)

### `POST /profile/update-name`

- Requires an active session
- Accepts form field: `name`
- On success → redirect to `/profile` (PRG pattern)
- On failure → re-render `profile.html` with a `name_error` variable

### `POST /profile/update-password`

- Requires an active session
- Accepts form fields: `current_password`, `new_password`, `confirm_password`
- On success → redirect to `/profile` with a `success` query param (`?updated=password`)
- On failure → re-render `profile.html` with a `password_error` variable

---

## 4. Auth Guard

Both `GET /profile` and any `POST /profile/*` route must redirect unauthenticated users:

- If `session.get("user_id")` is falsy → `redirect(url_for("login"))`
- Apply this check at the top of every handler before any DB access

---

## 5. Validation Rules

### Update name (`POST /profile/update-name`)

| Field | Rule |
| --- | --- |
| name | Required, not blank after stripping whitespace, max 100 characters |

### Update password (`POST /profile/update-password`)

| Field | Rule |
| --- | --- |
| current_password | Required, must match the stored hash |
| new_password | Required, minimum 8 characters |
| confirm_password | Required, must match `new_password` exactly |

- Validate field presence before any DB operation
- Verify `current_password` against the stored hash before updating
- Check `new_password == confirm_password` before hashing

---

## 6. Database Operations

### Fetch user (GET /profile)

```sql
SELECT id, name, email, created_at FROM users WHERE id = ?
```

Pass `session["user_id"]` as the parameter.

### Update name

```sql
UPDATE users SET name = ? WHERE id = ?
```

After a successful update, also sync `session["user_name"]` to the new name.

### Update password

```sql
SELECT password_hash FROM users WHERE id = ?   -- to verify current password
UPDATE users SET password_hash = ? WHERE id =? -- after verification passes
```

Use parameterized queries only — no string formatting in SQL.

---

## 7. Error Messages

### Name update errors

| Condition | Variable | Message |
| --- | --- | --- |
| Name is blank | `name_error` | "Name cannot be blank." |
| Name exceeds 100 characters | `name_error` | "Name must be 100 characters or fewer." |

### Password update errors

| Condition | Variable | Message |
| --- | --- | --- |
| Any required field is empty | `password_error` | "All fields are required." |
| `current_password` is wrong | `password_error` | "Current password is incorrect." |
| `new_password` shorter than 8 chars | `password_error` | "New password must be at least 8 characters." |
| `confirm_password` does not match | `password_error` | "Passwords do not match." |

### Success feedback

- On successful password update, redirect to `/profile?updated=password`
- The template reads `request.args.get("updated")` and shows a success banner when the value is `"password"`
- On successful name update, redirect to `/profile?updated=name` and show the same banner with a different message

---

## 8. Template — `profile.html`

Extends `base.html`. Uses only existing CSS classes from `style.css`.

### Layout

```
<main class="profile-page">
  <!-- Account info card -->
  <section class="card">
    <h2>Account</h2>
    <p>Email: {{ user.email }}</p>
    <p>Member since: {{ user.created_at }}</p>
  </section>

  <!-- Update name card -->
  <section class="card">
    <h2>Display Name</h2>
    {% if name_error %}<p class="auth-error">{{ name_error }}</p>{% endif %}
    <form method="POST" action="/profile/update-name">
      <input type="text" name="name" value="{{ user.name }}">
      <button type="submit" class="btn-submit">Save</button>
    </form>
  </section>

  <!-- Change password card -->
  <section class="card">
    <h2>Change Password</h2>
    {% if password_error %}<p class="auth-error">{{ password_error }}</p>{% endif %}
    {% if request.args.get('updated') %}<p class="success-msg">...</p>{% endif %}
    <form method="POST" action="/profile/update-password">
      <input type="password" name="current_password" placeholder="Current password">
      <input type="password" name="new_password" placeholder="New password">
      <input type="password" name="confirm_password" placeholder="Confirm new password">
      <button type="submit" class="btn-submit">Update Password</button>
    </form>
  </section>
</main>
```

- Do not add new global CSS classes — use `.card`, `.btn-submit`, `.auth-error` from `style.css`
- Add a `.success-msg` rule scoped to `profile.html` only if `.auth-error` color is insufficient; otherwise reuse an existing utility

---

## 9. Files to Change

- `app.py` — replace the `GET /profile` stub; add `POST /profile/update-name` and `POST /profile/update-password` routes

---

## 10. Files to Create

- `templates/profile.html` — profile page template extending `base.html`

---

## 11. Dependencies

- No new pip packages
- Use:
  - `flask`: `request`, `redirect`, `url_for`, `session` (already imported)
  - `werkzeug.security`: `check_password_hash`, `generate_password_hash` (already imported)
  - `database.db`: `get_db` (already imported)

---

## 12. Rules for Implementation

- Use parameterized queries only — never string-format SQL
- Validate all fields before opening a database connection
- Close the database connection after every query (use `db.close()` or a `try/finally` block)
- Apply the auth guard at the top of every handler before any other logic
- Follow the PRG (Post/Redirect/Get) pattern on all successful POST operations
- Sync `session["user_name"]` after a successful name update
- Do not use Flask-Login, Flask-WTF, or any additional auth library

---

## 13. Expected Behavior

- Visiting `/profile` while logged out redirects to `/login`
- Visiting `/profile` while logged in shows the user's name, email, and join date
- Submitting a valid new name updates it in the DB, syncs the session, and redirects back to `/profile`
- Submitting a blank name re-renders the page with `name_error`
- Submitting the correct current password plus a valid matching new password updates the hash and redirects to `/profile?updated=password`
- Submitting a wrong `current_password` re-renders with `password_error`
- Submitting mismatched `new_password`/`confirm_password` re-renders with `password_error`
- The success banner is visible only when `?updated=` is present in the URL

---

## 14. Definition of Done

- [ ] `GET /profile` redirects unauthenticated users to `/login`
- [ ] `GET /profile` renders `profile.html` with the logged-in user's data
- [ ] `profile.html` displays name, email, and `created_at`
- [ ] `POST /profile/update-name` validates name before any DB operation
- [ ] Successful name update persists to DB, syncs session, and redirects to `/profile?updated=name`
- [ ] Failed name update re-renders `profile.html` with a non-empty `name_error`
- [ ] `POST /profile/update-password` validates all three fields before any DB operation
- [ ] Wrong `current_password` returns the correct `password_error` message
- [ ] Mismatched passwords return the correct `password_error` message
- [ ] Successful password update stores a new hash and redirects to `/profile?updated=password`
- [ ] Success banner is shown when `?updated=` param is present
- [ ] All SQL uses parameterized queries
- [ ] No new pip packages introduced
