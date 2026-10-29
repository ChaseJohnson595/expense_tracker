# Expense Tracker Web App Plan

## Goal

Evolve the expense tracker into a web app that can first be used privately and
then, if desired, safely support multiple users. Keep the existing CLI working,
reuse the expense domain rules, and practice an incremental, reviewable software
delivery process.

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
- [ ] Reconcile the status and remaining work in `docs/plan.md` with the
  current implementation before building on it.

## Scope and principles

- Keep the CLI as a supported interface while adding the web interface.
- Keep HTTP handlers thin: validate/request-bind input, call application
  operations, and render responses. Do not put expense calculations or
  persistence logic in route handlers.
- Reuse existing model validation and expense behavior where appropriate.
- Start with a private, single-user deployment. Do not treat a shared login as
  multi-user support.
- Add user accounts and per-user data ownership before allowing multiple
  people to use the same deployment.
- Use SQLite for local development and private prototyping. Plan for PostgreSQL
  before a hosted multi-user launch.
- Ask before adding the web framework or any other dependency, consistent with
  the project dependency policy.

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

- [ ] Compare `docs/plan.md` with the current source, tests, and README; update
  stale completion status or open tasks.
- [ ] Decide whether JSON-path storage compatibility is still needed, and
  document the supported storage interface for future web code.
- [ ] Identify the functions the web interface can call for adding, listing,
  summarizing, and deleting expenses.
- [ ] Record any missing test coverage that blocks safely reusing those
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

### 4. Run privately and establish basic operations

- [ ] Choose a private initial hosting or local-network setup; do not expose
  the app publicly without access control.
- [ ] Confirm the chosen host has durable storage before using SQLite there.
- [ ] Configure the database location outside the source tree and keep database
  files out of version control.
- [ ] Document how to start and stop the app, where its data lives, and how to
  make and restore a backup.
- [ ] Test the deployed app and verify expenses persist across restarts.

### 5. Add multi-user support before inviting other users

- [ ] Choose an authentication approach and define account creation,
  sign-in, sign-out, and account recovery expectations.
- [ ] Add a user identity and associate every expense with its owner.
- [ ] Ensure every expense read, summary, filter, update, and delete is scoped
  to the signed-in user.
- [ ] Add database migrations for the user and ownership schema changes,
  including a deliberate strategy for existing single-user expenses.
- [ ] Protect sessions and credentials using framework-supported mechanisms;
  never store secrets in source control.
- [ ] Add tests proving users cannot view, summarize, or delete another user's
  expenses, as well as tests for unauthenticated access.
- [ ] Review authorization behavior before making the deployment available to
  other people.

### 6. Prepare for hosted multi-user use

- [ ] Add PostgreSQL support and use migrations to manage schema changes.
- [ ] Test database behavior against the production database engine rather
  than relying only on SQLite tests.
- [ ] Configure HTTPS, secure session settings, and production secrets through
  the hosting environment.
- [ ] Establish automated backups and verify restoration from a backup.
- [ ] Add operational logging and a way to detect application or database
  failures without logging sensitive expense details.
- [ ] Document deployment, upgrades, rollback expectations, data retention,
  and account/data deletion behavior.
- [ ] Run the complete test suite and lint checks before release.

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
- Authentication and per-user authorization before multi-user use.
- Database migrations and ownership behavior when PostgreSQL support is added.

## Completion criteria

- The existing CLI remains usable and shares the same validated expense
  behavior as the web interface.
- A private single-user web MVP can create, list, filter, summarize, and delete
  expenses with clear success and error responses.
- The app's data location, startup procedure, and backup/restore procedure are
  documented.
- Multi-user access is not enabled until authentication, ownership enforcement,
  migration behavior, and cross-user isolation tests are in place.
- A hosted multi-user release uses durable PostgreSQL storage, secure
  configuration, HTTPS, and a tested backup/restore process.
- The test suite and Ruff checks pass for each completed implementation phase.
