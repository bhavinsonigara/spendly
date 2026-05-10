## 1. Overview

Implement user registration by wiring the `POST /register` route in `app.py`.

This step covers the full registration flow: reading form data, validating input, hashing the password, inserting the user into the database, and redirecting on success or re-rendering the form on failure.

---

## 2. Depends on

- Step 1 — `database/db.py` must be complete (`get_db()`, `init_db()`, `seed_db()` all working, `users` table created)

---

## 3. Routes

### `POST /register`

- Accepts form fields: `name`, `email`, `password`
- On success → redirect to `/login`
- On failure → re-render `register.html` with an `error` variable

The existing `GET /register` route in `app.py` remains unchanged.

---

## 4. Validation Rules

All validation happens server-side inside the `POST /register` handler.

| Field | Rule |
| --- | --- |
| name | Required, not blank after stripping whitespace |
| email | Required, not blank after stripping whitespace |
| password | Required, minimum 8 characters |
| email | Must not already exist in the `users` table |

- Check fields are present and non-empty before hitting the database
- Check for duplicate email after basic validation passes
- Return a single, user-facing error message string for each failure case

---

## 5. Password Handling

- Hash the password using `werkzeug.security.generate_password_hash` before inserting
- Never store the plain-text password
- Store only the resulting hash in the `password_hash` column

---

## 6. Database Operation

- Insert a new row into the `users` table with: `name`, `email`, `password_hash`
- `created_at` is handled automatically by the column default
- Use parameterized queries only — no string formatting in SQL

---

## 7. Error Messages

Return a descriptive plain-text string as the `error` template variable for each failure case:

| Condition | Error message |
| --- | --- |
| Any required field is empty | "All fields are required." |
| Password shorter than 8 characters | "Password must be at least 8 characters." |
| Email already registered | "An account with that email already exists." |

---

## 8. Files to Change

- `app.py` — add `POST` method to the existing `/register` route; import `request`, `redirect`, `url_for`, `generate_password_hash`, and `get_db`

---

## 9. Files to Create

- None

---

## 10. Dependencies

- No new pip packages
- Use:
  - `flask`: `request`, `redirect`, `url_for` (add to existing Flask import)
  - `werkzeug.security`: `generate_password_hash` (already installed)
  - `database.db`: `get_db` (already imported)

---

## 11. Rules for Implementation

- Use parameterized queries only — never string-format SQL
- Hash password before any database write
- Validate all fields before opening a database connection
- Close the database connection after the insert (use `db.close()` or a `try/finally` block)
- Do not use Flask-Login, Flask-WTF, or any additional auth library

---

## 12. Expected Behavior

- Submitting a valid form creates a new user and redirects to `/login`
- Submitting with a blank field re-renders `register.html` with the appropriate error message
- Submitting a password shorter than 8 characters re-renders with the appropriate error message
- Submitting a duplicate email re-renders with the appropriate error message
- The `register.html` template already renders `{{ error }}` inside `.auth-error` — no template changes needed

---

## 13. Error Handling Expectations

- Duplicate email → caught by querying the DB before insert; returns user-facing error (do not rely solely on the UNIQUE constraint exception)
- DB errors → allowed to propagate as unhandled exceptions for now (no custom 500 page required at this step)

---

## 14. Definition of Done

- [ ] `POST /register` route exists alongside the existing `GET /register` route
- [ ] All three fields are validated before any DB operation
- [ ] Password length is enforced (minimum 8 characters)
- [ ] Duplicate email check returns the correct error message
- [ ] Password is stored as a hash, never plain-text
- [ ] Successful registration redirects to `/login`
- [ ] All failure cases re-render `register.html` with a non-empty `error` variable
- [ ] All SQL uses parameterized queries
