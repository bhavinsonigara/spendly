## 1. Overview

Implement user login and logout by wiring the `POST /login` and `GET /logout` routes in `app.py`.

Login covers the full authentication flow: reading form data, validating input, verifying the password hash, starting a session, and redirecting on success or re-rendering the form on failure. Logout tears down the session and redirects to the landing page.

---

## 2. Depends on

- Step 1 — `database/db.py` must be complete (`get_db()` working, `users` table created)
- Step 2 — Registration must be complete so that real user accounts exist to log into

---

## 3. Routes

### `POST /login`

- Accepts form fields: `email`, `password`
- On success → redirect to `/expenses`
- On failure → re-render `login.html` with an `error` variable

The existing `GET /login` route in `app.py` remains unchanged.

### `GET /logout`

- Clears the session
- Redirects to `/`

---

## 4. Validation Rules

All validation happens server-side inside the `POST /login` handler.

| Field | Rule |
| --- | --- |
| email | Required, not blank after stripping whitespace |
| password | Required, not blank |

- Check fields are present and non-empty before hitting the database
- Look up the user by email; if not found → return a generic error
- Verify the submitted password against the stored hash; if mismatch → return a generic error
- Always return the same generic message for both "user not found" and "wrong password" to avoid user enumeration

---

## 5. Session Handling

### On successful login

- Store the following in `session`:
  - `user_id` — the user's integer primary key
  - `user_name` — the user's display name

### On logout

- Call `session.clear()` to remove all session data
- Do not selectively pop keys — clear everything

---

## 6. Password Verification

- Use `werkzeug.security.check_password_hash(stored_hash, submitted_password)` to verify
- Never compare plain-text passwords directly
- Retrieve the `password_hash` column from the `users` row before calling the check

---

## 7. Error Messages

Return a descriptive plain-text string as the `error` template variable for each failure case:

| Condition | Error message |
| --- | --- |
| Any required field is empty | "All fields are required." |
| Email not found or password incorrect | "Invalid email or password." |

---

## 8. Files to Change

- `app.py` — add `POST` method to the existing `/login` route; implement `GET /logout`; import `session`, `check_password_hash`, and ensure `secret_key` is set on the app

---

## 9. Files to Create

- None

---

## 10. Dependencies

- No new pip packages
- Use:
  - `flask`: `request`, `redirect`, `url_for`, `session` (add to existing Flask import)
  - `werkzeug.security`: `check_password_hash` (already installed)
  - `database.db`: `get_db` (already imported)

---

## 11. Rules for Implementation

- Use parameterized queries only — never string-format SQL
- Validate fields before opening a database connection
- Close the database connection after the query (use `db.close()` or a `try/finally` block)
- Do not use Flask-Login, Flask-WTF, or any additional auth library
- `app.secret_key` must be set for session to work — set it once at app initialization if not already present
- Use a generic error for both wrong email and wrong password (no user enumeration)

---

## 12. Expected Behavior

- Submitting valid credentials starts a session and redirects to `/expenses`
- Submitting with a blank field re-renders `login.html` with the appropriate error message
- Submitting an unrecognized email re-renders `login.html` with the generic invalid credentials message
- Submitting the wrong password re-renders `login.html` with the same generic invalid credentials message
- Visiting `/logout` clears the session and redirects to `/`
- The `login.html` template already renders `{{ error }}` inside `.auth-error` — no template changes needed

---

## 13. Error Handling Expectations

- DB errors → allowed to propagate as unhandled exceptions for now (no custom 500 page required at this step)
- Missing `secret_key` → will cause a runtime error; ensure it is set before routes are used

---

## 14. Definition of Done

- [ ] `POST /login` route exists alongside the existing `GET /login` route
- [ ] Both fields are validated before any DB operation
- [ ] Wrong credentials (any combination) return the generic error message
- [ ] Successful login stores `user_id` and `user_name` in the session
- [ ] Successful login redirects to `/expenses`
- [ ] All failure cases re-render `login.html` with a non-empty `error` variable
- [ ] `GET /logout` clears the entire session
- [ ] `GET /logout` redirects to `/`
- [ ] All SQL uses parameterized queries
- [ ] `app.secret_key` is set
