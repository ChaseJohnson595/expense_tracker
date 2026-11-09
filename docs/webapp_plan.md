# Expense Tracker Web App Plan

## Goal

Evolve the expense tracker into a web app for local use first, then make it
available to the owner and a small group of trusted people on a private LAN.
Keep the existing CLI working, reuse the expense domain rules, and practice an
incremental, reviewable software delivery process. Commercial product work and
public internet hosting are not goals for this plan.

The initial web stack is FastAPI with server-rendered pages. This keeps the
first version in Python and avoids requiring a separate frontend build.

## Status key

- `[x]` Complete
- `[ ]` Not complete

## Technology stack

- **Python:** Continue using the project's supported Python version
  (currently Python 3.12 or later, as declared in `pyproject.toml`).
- **FastAPI:** Define the web application and routes, bind and validate HTTP
  input, and construct responses. Route handlers call existing model and
  storage operations rather than implementing expense rules or persistence.
- **Uvicorn:** Run the FastAPI ASGI application. The local development command
  is `.venv\Scripts\uvicorn.exe expense_tracker.web:app --reload`; reload is
  for development, not the LAN deployment command.
- **Jinja2:** Render HTML on the server without a separate frontend build.
  Keep templates in `src/expense_tracker/templates/` and include them as
  package data so they are available when the application is installed.
- **httpx2:** Provide the HTTP client used by FastAPI's test client. It is a
  test dependency, not a production server component.
- **SQLite:** Continue using the existing storage module and host-local
  database. Use the existing default path unless `EXPENSE_TRACKER_DB_PATH`
  overrides it; do not commit database files or secrets.
- **Tests and lint:** Continue using pytest and Ruff. Keep web tests isolated
  from the user's database with temporary databases and test configuration.

FastAPI, Uvicorn, and Jinja2 are approved application dependencies; httpx2 is
approved for tests. Declare application dependencies in project metadata and
httpx2 with the development/test dependencies. Do not add a frontend framework,
build system, or other dependencies without a clear need and approval.

## Existing foundation

- [x] Define expenses with integer-cent amounts, validated categories, ISO
  dates, and optional notes.
- [x] Separate CLI argument parsing and output from expense models and storage.
- [x] Use SQLite for the default local storage backend and cover core behavior
  with tests.
- [x] Reconcile the SQLite migration status in `docs/plan.md` with the current
  implementation.
- [x] Decide to remove the legacy behavior where an explicitly supplied
  `.json` data path uses JSON storage, while retaining JSON import into SQLite.
- [x] Remove JSON-backed ongoing storage and ensure SQLite is the sole storage
  backend before web integration.

## Scope and principles

- Keep the CLI as a supported interface while adding the web interface.
- Keep HTTP handlers thin: validate/request-bind input, call application
  operations, and render responses. Do not put expense calculations or
  persistence logic in route handlers.
- Reuse existing model validation and expense behavior where appropriate.
- Build and verify the app locally before allowing LAN access.
- Use SQLite on the host machine's local durable disk for the planned LAN
  deployment. Do not put the database file on a network share or ephemeral
  filesystem.
- Choose whether LAN users share one ledger or need private individual
  expenses before enabling access for other people. Implement data ownership
  and per-user authorization only if the latter is required.
- Restrict access to the private network and require appropriate access
  controls; trusted users do not replace network or application security.
- Use only the approved web dependencies listed in the technology stack;
  ask before introducing additional dependencies.
- Revisit hosted deployment, PostgreSQL, or commercial-readiness work only if
  the intended use changes.

## Architecture

- `src/expense_tracker/models.py`: Keep expense types, validation, and
  calculations independent of HTTP and presentation concerns.
- `src/expense_tracker/storage.py`: Own SQLite persistence for all ongoing
  expense operations. Keep JSON support limited to importing existing records
  into SQLite.
- `src/expense_tracker/`: Add a web application module for FastAPI routes and
  configuration. Keep request/response concerns out of the CLI and storage.
- `src/expense_tracker/templates/` and, if needed,
  `src/expense_tracker/static/`: Store package-local templates and assets.
- `tests/`: Cover web behavior independently from existing model, storage, and
  CLI tests.

Keep the initial implementation simple. Introduce a separate application
service layer only if it provides a clear shared boundary for CLI and web
operations; do not duplicate business rules between the two interfaces.

## Implementation sequence

### 1. Clarify the current application boundary

- [x] Compare `docs/plan.md` with the current source, tests, and README; update
  stale completion status or open tasks.
- [x] Decide to remove JSON-path storage compatibility, retain JSON import, and
  document SQLite as the sole ongoing storage backend.
- [x] Remove the legacy JSON-backed path behavior while preserving the
  `import-json` migration command.
- [x] Identify the functions the web interface can call for adding, listing,
  summarizing, and deleting expenses.
- [x] Record any missing test coverage that blocks safely reusing those
  operations.

### 2. Establish the web application skeleton

- [x] Confirm FastAPI with server-rendered pages, Uvicorn, Jinja2, and httpx2
  for tests as the initial stack.
- [x] Add an application entry point that can be run locally without changing
  the existing CLI entry point.
- [x] Add a basic health or home route and a minimal page template.
- [x] Keep database path and other environment-specific settings configurable
  without committing secrets; use `EXPENSE_TRACKER_DB_PATH` to override the
  existing database default.
- [x] Add focused tests for application startup, route responses, and error
  handling.
- [x] Document local development and run commands, including
  `.venv\Scripts\uvicorn.exe expense_tracker.web:app --reload` for local use.

### 3. Deliver the private, single-user web MVP

- [x] Add a form for creating an expense using existing validation rules.
- [x] Show expenses newest first, with the existing date-range and category
  filters where practical.
- [x] Show the monthly total and category totals using integer cents.
- [x] Provide deletion with an explicit confirmation to reduce accidental data
  loss.
- [x] Display validation and storage errors clearly; do not report success if
  persistence failed.
- [x] Add tests for successful requests, invalid input, filtering, summaries,
  deletion, and storage failures.
- [x] Verify the CLI continues to work against the same local data.

### 4. Verify local operation and establish basic data safety

- [x] Run the app locally and verify expenses persist across restarts.
- [x] Configure the database location outside the source tree and keep database
  files out of version control.
- [x] Document how to start and stop the app, where its data lives, and how to
  make and restore a backup.
- [x] Test restoring a backup before relying on the app for personal records.

### 5. Choose the LAN sharing model

- [ ] Decide whether everyone on the LAN uses one shared ledger or each person
  needs private expense records.
- [ ] For a shared ledger, define who can view, add, and delete records, and
  whether changes need to be attributable to a person.
- [ ] For private records, design accounts and owner-scoped storage before
  enabling LAN access; scope every read, summary, filter, update, and delete to
  the signed-in user.
- [ ] Choose access controls appropriate for the selected model, protect
  credentials and sessions, and keep secrets out of source control.
- [ ] Add tests for the selected authorization rules, including cross-user
  isolation if private records are supported.

### 6. Deploy to a private LAN

- [ ] Select a host that can remain available to LAN users and has durable
  local storage for the SQLite database.
- [ ] Configure the app to listen only on the intended LAN interface and
  restrict inbound access with the host firewall or equivalent network rules.
- [ ] Use an authenticated, protected connection appropriate to the LAN setup;
  do not expose the app directly to the public internet.
- [ ] Configure reliable startup/restart behavior and document how to update
  and stop the app.
- [ ] Configure backups on the host and periodically verify restoration.
- [ ] Test from each intended type of client and verify access restrictions,
  persistence across restarts, and the selected sharing/authorization model.
- [ ] Run the complete test suite and Ruff checks before inviting other users.

## Out of scope unless the goal changes

- Public internet access or commercial launch.
- Hosted-app platforms and deployment automation for public production.
- PostgreSQL migration; the planned LAN setup uses SQLite on the application
  host's local disk.
- Multi-user accounts and private per-user records if the group explicitly
  chooses a shared ledger instead.

## Tests

Keep web tests isolated from the real per-user database and external services.
Use temporary databases and a test configuration. Cover:

- App creation, route responses, and user-visible errors.
- Expense creation with valid and invalid amounts, categories, and dates.
- Listing and filtering by date and category.
- Monthly summaries calculated from integer-cent amounts.
- Deletion and confirmation behavior.
- Persistence errors and failed operations that must not return success.
- CLI behavior remaining intact as the web interface is introduced.
- LAN access controls and sharing-model authorization before other people use
  the deployment.
- Cross-user isolation if the selected model includes private user records.

## Completion criteria

- The existing CLI remains usable and shares the same validated expense
  behavior as the web interface.
- A private single-user web MVP can create, list, filter, summarize, and delete
  expenses with clear success and error responses.
- The app's data location, startup procedure, and backup/restore procedure are
  documented.
- The LAN sharing model is explicitly chosen, and matching access controls and
  tests are in place before other people use the app.
- The LAN deployment uses durable host-local storage, restricted network
  access, documented startup/restart procedures, and a tested backup/restore
  process.
- The test suite and Ruff checks pass for each completed implementation phase.
