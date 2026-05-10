---
description: Create a single dummy user in the database
allowed-tools: Bash(python:*)
---

Insert a new dummy user into `spendly.db`. Password is always `demo123`.

Start with `demo@spendly.com`. If that email already exists, try `demo2@spendly.com`, `demo3@spendly.com`, and so on until a free slot is found, then insert.

Run this Python snippet (venv already activated via `source D:/expense-tracker/venv/Scripts/activate`):

```bash
source D:/expense-tracker/venv/Scripts/activate && python - <<'EOF'
import sys, os
sys.path.insert(0, 'D:/expense-tracker')
from database.db import get_db, init_db
from werkzeug.security import generate_password_hash

init_db()
conn = get_db()

base = "demo"
domain = "@spendly.com"
candidate = base + domain
i = 2
while conn.execute("SELECT id FROM users WHERE email = ?", (candidate,)).fetchone():
    candidate = f"{base}{i}{domain}"
    i += 1

name = "Demo User" if i == 2 else f"Demo User {i - 1}"
conn.execute(
    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
    (name, candidate, generate_password_hash("demo123")),
)
conn.commit()
user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
print(f"Created user: {name} <{candidate}> (id={user_id})")
conn.close()
EOF
```
