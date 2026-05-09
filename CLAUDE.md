# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server (http://localhost:5001)
python app.py

# Run tests
pytest

# Run a specific test file
pytest tests/test_auth.py
```

## Architecture

**Spendly** is a Flask-based expense tracker. The backend is Python/Flask with SQLite; the frontend is Jinja2 templates + vanilla JS + a single unified CSS file.

### Key files

- `app.py` — all routes; routes marked with `# Step N:` comments are stubs awaiting implementation
- `database/db.py` — database initialization and helpers (Step 1 of the implementation)
- `templates/base.html` — base template; navbar and footer live here
- `static/css/style.css` — the only stylesheet; uses CSS custom properties for the design system

### Route structure

Routes are registered directly in `app.py`. Completed routes render templates; stub routes are placeholders for Steps 3–9:

| Step | Route | Description |
|------|-------|-------------|
| done | `GET /` | Landing page |
| done | `GET /register`, `GET /login` | Auth form pages |
| 1 | `database/db.py` | SQLite setup |
| 2 | `POST /register`, `POST /login` | Auth logic |
| 3 | `GET /logout` | Session teardown |
| 4 | `GET /profile` | User profile |
| 5–6 | `GET /expenses` | Dashboard / listing |
| 7 | `POST /expenses/add` | Create expense |
| 8 | `POST /expenses/<id>/edit` | Update expense |
| 9 | `POST /expenses/<id>/delete` | Delete expense |

### Frontend design system

All UI tokens are CSS custom properties defined at the top of `style.css`:

- Colors: `--ink` (#0f0f0f), `--paper` (#f7f6f3), `--green` (#1a472a), `--accent-2` (#c17f24), `--danger` (#c0392b)
- Fonts: DM Serif Display (headings), DM Sans (body) — loaded from Google Fonts in `base.html`
- Shared component classes: `.btn-primary`, `.btn-ghost`, `.btn-submit`, `.modal`, `.card`
- Responsive breakpoints: 900px (tablet), 600px (mobile)

New pages should extend `base.html` and use these existing classes rather than adding new global styles.
