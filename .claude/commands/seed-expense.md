---
description: Seed relaistic dummy expenses for dummy user
argument-hint: "<user_id> <count> <months>"
allowed-tools: Read, Bash(Python3:*)
---

Read @database/db.py to understand the expenses table schema, the db connection pattern and database file name.

User input: $ARGUMENTS

## Step 1 - Parse arguments

Parse `$ARGUMENTS` as three positional values: `user_id` (integer), `count` (integer, number of expenses to insert), and `months` (integer, how many past months to spread the expenses across). If any argument is missing or not a valid integer, print a usage error and stop:
```
Usage: /seed-expense <user_id> <count> <months>
```

## Step 2 - Verify user exists

Query the `users` table for a row with the given `user_id`. If no row is found, print an error and stop:
```
Error: No user found with id=<user_id>
```

## Step 3 - Generate and insert expenses

Generate `count` realistic expense records spread randomly across the last `months` months (from today back). For each record:

- `user_id` — the verified user's id
- `amount` — a realistic float between 2.00 and 300.00 (rounded to 2 decimal places)
- `category` — chosen randomly from: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`
- `date` — a random date (as `YYYY-MM-DD`) within the last `months` months
- `description` — a short realistic description that matches the category (e.g. "Weekly groceries" for Food, "Bus pass" for Transport)

Insert all records in a single `executemany` call.

## Step 4 - Confirm

Print:
- How many expenses were inserted
- The date range they span
- A sample of 5 inserted records