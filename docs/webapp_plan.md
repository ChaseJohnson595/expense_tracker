# Expense Tracker Web App Plan

## Goal

Evolve the expense tracker into a web app for local use first, then make it
available to the owner and a small group of trusted people on a private LAN.
Keep the existing CLI working, reuse the expense domain rules, and practice an
incremental, reviewable software delivery process. Commercial product work and
public internet hosting are not goals for this plan.

The proposed first web stack is FastAPI with server-rendered pages. This keeps
the first version in Python and avoids requiring a separate frontend build.
Revisit the framework choice before implementation if learning Django or a
separate frontend is a higher priority.

## Status key

- `[x]` Complete
- `[ ]` Not complete

## Existing foundation

- [x] Define expenses with integer-cent amounts, validated categories, ISO
  dates, and optional notes.
- [x] Separate CLI argument parsing and output from expense models and storage.
- [x] Use SQLite for the default local storage backend and cover core behavior
  with tests.
- [x] Reconcile the SQLite migration status in `docs/plan.md` with the current
  implementation.
- [ ] Decide whether to remove or intentionally retain the legacy behavior
  where an explicitly supplied `.json` data path uses JSON storage.

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
- Ask before adding the web framework or any other dependency, consistent with
  the project dependency policy.
- Revisit hosted deployment, PostgreSQL, or commercial-readiness work only if
  the intended use changes.

## Architecture

- `src/expense_tracker/models.py`: Keep expense types, validation, and
  calculations independent of HTTP and presentation concerns.
- `src/expense_tracker/storage.py`: Continue to own persistence. Add or adapt
  operations only where the web application needs them.
- `src/expense_tracker/`: Add a web application module for FastAPI routes and
  configuration. Keep request/response concerns out of the CLI and storage.
- `templates/` and `static/`: Store server-rendered page templates and
  application assets if needed.
- `tests/`: Cover web behavior independently from existing model, storage, and
  CLI tests.

Keep the initial implementation simple. Introduce a separate application
service layer only if it provides a clear shared boundary for CLI and web
operations; do not duplicate business rules between the two interfaces.

## Implementation sequence

### 1. Clarify the current application boundary

- [x] Compare `docs/plan.md` with the current source, tests, and README; update
  stale completion status or open tasks.
- [ ] Decide whether JSON-path storage compatibility is still needed, and
  document the supported storage interface for future web code.
- [x] Identify the functions the web interface can call for adding, listing,
  summarizing, and deleting expenses.
- [x] Record any missing test coverage that blocks safely reusing those
  operations.

### 2. Establish the web application skeleton

- [ ] Confirm FastAPI with server-rendered pages as the initial framework
  choice; ask before adding its dependency.
- [ ] Add an application entry point that can be run locally without changing
  the existing CLI entry point.
- [ ] Add a basic health or home route and a minimal page template.
- [ ] Keep database path and other environment-specific settings configurable
  without committing secrets.
- [ ] Add focused tests for application startup, route responses, and error
  handling.
- [ ] Document local development and run commands.

### 3. Deliver the private, single-user web MVP

- [ ] Add a form for creating an expense using existing validation rules.
- [ ] Show expenses newest first, with the existing date-range and category
  filters where practical.
- [ ] Show the monthly total and category totals using integer cents.
- [ ] Provide deletion with an explicit confirmation to reduce accidental data
  loss.
- [ ] Display validation and storage errors clearly; do not report success if
  persistence failed.
- [ ] Add tests for successful requests, invalid input, filtering, summaries,
  deletion, and storage failures.
- [ ] Verify the CLI continues to work against the same local data.

### 4. Verify local operation and establish basic data safety

- [ ] Run the app locally and verify expenses persist across restarts.
- [ ] Configure the database location outside the source tree and keep database
  files out of version control.
- [ ] Document how to start and stop the app, where its data lives, and how to
  make and restore a backup.
- [ ] Test restoring a backup before relying on the app for personal records.

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
