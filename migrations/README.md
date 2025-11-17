# Database Migrations

This folder contains SQL migration scripts for the WMS database.

## How to Run Migrations

Since this project uses SQLite directly (no Flask-Migrate), migrations must be run manually:

### Method 1: Using sqlite3 command line

```bash
# From project root
sqlite3 data.db < migrations/add_handover_code_fields.sql
```

### Method 2: Using Python script

```python
import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

with open('migrations/add_handover_code_fields.sql', 'r') as f:
    cursor.executescript(f.read())

conn.commit()
conn.close()
print("Migration completed!")
```

### Method 3: Using Flask shell

```python
from app import create_app, db

app = create_app()
with app.app_context():
    with open('migrations/add_handover_code_fields.sql', 'r') as f:
        for statement in f.read().split(';'):
            if statement.strip():
                db.session.execute(statement)
    db.session.commit()
    print("Migration completed!")
```

## Migration History

| Date       | File                            | Description                          |
|------------|---------------------------------|--------------------------------------|
| 2025-11-16 | add_handover_code_fields.sql   | Add Handover Code System to Batch    |

## Notes

- Always backup `data.db` before running migrations
- Test migrations on a development database first
- Verify migration success by checking the "migrated" count in the output
