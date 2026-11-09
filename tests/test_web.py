from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from expense_tracker.models import Expense
from expense_tracker.storage import (
    StorageError,
    add_expense,
    get_database_path,
    list_expenses,
)
from expense_tracker.web import app


@pytest.fixture(autouse=True)
def use_temporary_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        app.state,
        "database_path",
        str(tmp_path / "expenses.sqlite3"),
        raising=False,
    )


def test_application_entry_point_starts() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Expense Tracker"


def test_health_route_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_route_renders_minimal_page() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<h2 id="add-expense-heading">Add an expense</h2>' in response.text
    assert 'name="amount"' in response.text
    assert 'name="category"' in response.text
    assert 'name="date"' in response.text
    assert 'name="note"' in response.text
    assert 'name="start_date"' in response.text
    assert 'name="end_date"' in response.text
    assert 'name="category"' in response.text


def test_home_lists_expenses_newest_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "expenses.sqlite3"
    monkeypatch.setattr(app.state, "database_path", str(database_path))
    add_expense(Expense(1250, "Food", "2026-11-07", "Older"), database_path)
    add_expense(Expense(250, "Transit", "2026-11-08", "Newer"), database_path)

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.text.index("Newer") < response.text.index("Older")
    assert "$2.50" in response.text
    assert "$12.50" in response.text


def test_home_shows_current_month_and_category_totals(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "expenses.sqlite3"
    monkeypatch.setattr(app.state, "database_path", str(database_path))
    today = date.today()
    previous_month = (
        date(today.year - 1, 12, 15)
        if today.month == 1
        else date(today.year, today.month - 1, 15)
    )
    add_expense(Expense(1250, "Food", today.isoformat()), database_path)
    add_expense(Expense(250, "Transit", today.isoformat()), database_path)
    add_expense(Expense(900, "Food", previous_month.isoformat()), database_path)

    with TestClient(app) as client:
        response = client.get("/", params={"category": "Transit"})

    assert response.status_code == 200
    assert f"Monthly summary for {today:%Y-%m}" in response.text
    assert "Total: $15.00" in response.text
    assert "Food: $12.50" in response.text
    assert "Transit: $2.50" in response.text
    assert "Previous month" not in response.text


def test_home_filters_expenses_by_inclusive_dates_and_category(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "expenses.sqlite3"
    monkeypatch.setattr(app.state, "database_path", str(database_path))
    add_expense(Expense(100, "Food", "2026-11-01", "Start"), database_path)
    add_expense(Expense(200, "Food", "2026-11-30", "End"), database_path)
    add_expense(Expense(300, "Transit", "2026-11-15", "Other category"), database_path)
    add_expense(Expense(400, "Food", "2026-12-01", "Outside range"), database_path)

    with TestClient(app) as client:
        response = client.get(
            "/",
            params={
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "category": " food ",
            },
        )

    assert response.status_code == 200
    assert "Start" in response.text
    assert "End" in response.text
    assert "Other category" not in response.text
    assert "Outside range" not in response.text
    assert 'value="2026-11-01"' in response.text
    assert 'value="2026-11-30"' in response.text
    assert 'value=" food "' in response.text


def test_delete_confirmation_does_not_remove_expense(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "expenses.sqlite3"
    monkeypatch.setattr(app.state, "database_path", str(database_path))
    expense = Expense(1250, "Food", "2026-11-08", "Lunch", id="food1234")
    add_expense(expense, database_path)

    with TestClient(app) as client:
        response = client.get(f"/expenses/{expense.id}/delete")
        cancel_response = client.get("/")

    assert response.status_code == 200
    assert "Confirm deletion" in response.text
    assert "Confirm deletion</button>" in response.text
    assert "Cancel</a>" in response.text
    assert cancel_response.status_code == 200
    assert list_expenses(database_path) == [expense]


def test_confirmed_delete_removes_expense(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "expenses.sqlite3"
    monkeypatch.setattr(app.state, "database_path", str(database_path))
    expense = Expense(1250, "Food", "2026-11-08", "Lunch", id="food1234")
    add_expense(expense, database_path)

    with TestClient(app) as client:
        client.get(f"/expenses/{expense.id}/delete")
        response = client.post(f"/expenses/{expense.id}/delete", follow_redirects=False)
        result = client.get(response.headers["location"])

    assert response.status_code == 303
    assert list_expenses(database_path) == []
    assert "Expense deleted successfully." in result.text


def test_home_rejects_reversed_date_filter(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(app.state, "database_path", str(tmp_path / "expenses.sqlite3"))

    with TestClient(app) as client:
        response = client.get(
            "/", params={"start_date": "2026-11-30", "end_date": "2026-11-01"}
        )

    assert response.status_code == 400
    assert "start_date must be on or before end_date" in response.text


def test_create_expense_form_saves_valid_expense(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "expenses.sqlite3"
    monkeypatch.setattr(app.state, "database_path", str(database_path))

    with TestClient(app) as client:
        response = client.post(
            "/",
            data={
                "amount": "12.50",
                "category": "Food",
                "date": "2026-11-08",
                "note": "Lunch",
            },
        )

    assert response.status_code == 200
    assert "Expense added successfully." in response.text
    saved_expenses = list_expenses(database_path)
    assert len(saved_expenses) == 1
    saved_expense = saved_expenses[0]
    assert saved_expense.amount_cents == 1250
    assert saved_expense.category == "Food"
    assert saved_expense.date == "2026-11-08"
    assert saved_expense.note == "Lunch"


def test_create_expense_form_displays_validation_error() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/",
            data={"amount": "0", "category": "Food", "date": "", "note": ""},
        )

    assert response.status_code == 400
    assert "amount must be greater than zero" in response.text
    assert 'value="0"' in response.text


def test_create_expense_form_displays_storage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_to_save(expense: Expense, data_path: Path | str | None = None) -> Expense:
        raise StorageError("Database is unavailable")

    monkeypatch.setattr("expense_tracker.web.add_expense", fail_to_save)
    with TestClient(app) as client:
        response = client.post(
            "/",
            data={"amount": "12.50", "category": "Food", "date": "", "note": ""},
        )

    assert response.status_code == 500
    assert "Could not save expense: Database is unavailable" in response.text
    assert "Expense added successfully." not in response.text


def test_unknown_route_returns_not_found() -> None:
    with TestClient(app) as client:
        response = client.get("/does-not-exist")

    assert response.status_code == 404


def test_database_path_uses_environment_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    override = tmp_path / "custom.sqlite3"
    monkeypatch.setenv("EXPENSE_TRACKER_DB_PATH", str(override))

    assert get_database_path() == override
