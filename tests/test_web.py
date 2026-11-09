from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from expense_tracker.models import Expense
from expense_tracker.storage import (
    StorageError,
    get_database_path,
    list_expenses,
)
from expense_tracker.web import app


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
