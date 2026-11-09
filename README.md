# Expense Tracker

A small command-line tool for recording, listing, summarizing, and deleting
personal expenses.

This is a learning project for practicing agent-assisted development and standard engineering habits: version control, testing, linting, and CI.

<img src=./docs/images/MVP_Refresh.png width="600">
<img src=./docs/images/11-08-2026_docs_endpoint_screenshot.png width="600">

## Requirements and setup

- Python 3.12 or later

Create and activate a virtual environment, then install the project:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

On macOS or Linux, activate the environment with
`source .venv/bin/activate`.

## Usage

Run commands with `python -m expense_tracker`:

```text
python -m expense_tracker add 12.50 --category food --note "Lunch"
python -m expense_tracker list
python -m expense_tracker list --start-date 2026-10-01 --end-date 2026-10-31 --category food
python -m expense_tracker summary
python -m expense_tracker summary --month 2026-10
python -m expense_tracker delete
python -m expense_tracker delete --month 2026-09
python -m expense_tracker import-json ./expenses.json
```

* `add` accepts an amount with at most two decimal places, a required category,
an optional `--date` in `YYYY-MM-DD` format, and an optional `--note`. If no
date is provided, today's date is used.
* `list` sorts newest dates first and accepts inclusive `--start-date` and
`--end-date` filters and a `--category` filter.
* `summary` defaults to the current month and reports integer-cent totals
overall and by category.
* `delete` displays a numbered menu of expenses from the current month. Use
`--month YYYY-MM` to choose another month. Choose an entry by number, or enter
`q` to exit without deleting anything.
* `import-json <path>` reads an existing JSON array of expense records and
imports them into SQLite. The source file is left unchanged, and JSON is not
used for ongoing storage.

Run `python -m expense_tracker --help` or
`python -m expense_tracker <command> --help` for command help.

## Data storage

Expenses are stored in SQLite at `~/.expense_tracker/expenses.sqlite3` (for
example, `%USERPROFILE%\.expense_tracker\expenses.sqlite3` on Windows). The
application creates the parent directory and database schema automatically when
needed. JSON remains an import-only format for migrating existing records into
SQLite; it is not used for ongoing storage.

When `EXPENSE_TRACKER_DB_PATH` is set, that path is used instead of the default.
Set it to the same value when starting the app and when running the backup or
restore steps below.

### Back up the database

Backups contain personal expense data. Store them somewhere private and separate
from the project directory. This PowerShell example creates a timestamped backup
under your user profile using SQLite's online backup API:

```powershell
$backupDirectory = Join-Path $HOME ".expense_tracker\backups"
New-Item -ItemType Directory -Force $backupDirectory | Out-Null
$env:EXPENSE_TRACKER_BACKUP_PATH = Join-Path $backupDirectory "expenses-$(Get-Date -Format 'yyyyMMdd-HHmmss').sqlite3"
@'
import os
import sqlite3
from pathlib import Path

database_path = Path(os.environ.get(
    "EXPENSE_TRACKER_DB_PATH",
    str(Path.home() / ".expense_tracker" / "expenses.sqlite3"),
)).expanduser()
backup_path = Path(os.environ["EXPENSE_TRACKER_BACKUP_PATH"]).expanduser()
if not database_path.is_file():
    raise FileNotFoundError(f"Database not found: {database_path}")
backup_path.parent.mkdir(parents=True, exist_ok=True)
source = sqlite3.connect(database_path)
destination = sqlite3.connect(backup_path)
try:
    source.backup(destination)
finally:
    destination.close()
    source.close()
print(f"Backup created: {backup_path}")
'@ | .\.venv\Scripts\python.exe -
```

### Restore a database backup

Stop the app first by pressing **Ctrl+C** in the terminal running Uvicorn. Set
`EXPENSE_TRACKER_BACKUP_PATH` to the backup file to restore. Restoring replaces
the active database contents; make a separate backup of the current database
first if you may need to recover it.

```powershell
$env:EXPENSE_TRACKER_BACKUP_PATH = Join-Path $HOME ".expense_tracker\backups\expenses-YYYYMMDD-HHMMSS.sqlite3"
@'
import os
import sqlite3
from pathlib import Path

database_path = Path(os.environ.get(
    "EXPENSE_TRACKER_DB_PATH",
    str(Path.home() / ".expense_tracker" / "expenses.sqlite3"),
)).expanduser()
backup_path = Path(os.environ["EXPENSE_TRACKER_BACKUP_PATH"]).expanduser()
if not backup_path.is_file():
    raise FileNotFoundError(f"Backup not found: {backup_path}")
source = sqlite3.connect(backup_path)
try:
    result = source.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"Backup integrity check failed: {result}")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    destination = sqlite3.connect(database_path)
    try:
        source.backup(destination)
        result = destination.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"Restored database integrity check failed: {result}")
    finally:
        destination.close()
finally:
    source.close()
print(f"Database restored: {database_path}")
'@ | .\.venv\Scripts\python.exe -
```

Start the app again using the local web app command below and check that the
expected expenses are present.

## Local web app

Start the app with:

```powershell
.venv\Scripts\uvicorn.exe expense_tracker.web:app --reload
```

The app listens on the default local FastAPI port (`127.0.0.1:8000`). To keep
the database in a custom location without committing secrets:

```powershell
$env:EXPENSE_TRACKER_DB_PATH = "$HOME\.expense_tracker\expenses.sqlite3"
.venv\Scripts\uvicorn.exe expense_tracker.web:app --reload
```

On macOS or Linux:

```bash
export EXPENSE_TRACKER_DB_PATH="$HOME/.expense_tracker/expenses.sqlite3"
.venv/bin/uvicorn expense_tracker.web:app --reload
```

In the web app, use an expense's **Delete** link to review the record before
confirming its deletion.

## Project structure

```
src/expense_tracker/
    cli.py        argument parsing and output
    models.py     data classes and validation
    storage.py    reading and writing data
tests/            one test file per module
docs/plan.md      design decisions and task checklist
```

## Development

Install the development tools in the active environment if needed:

```text
python -m pip install pytest ruff
```

Run tests and lint:

```text
python -m pytest -q
ruff check .
```

Amounts are stored as integer cents and dates as ISO 8601 strings
(`YYYY-MM-DD`). Business logic lives outside the CLI. See [docs/plan.md](docs/plan.md)
for the design and implementation plan.
