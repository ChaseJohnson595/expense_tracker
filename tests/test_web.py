from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from expense_tracker.storage import get_database_path
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
    assert "<h1>Expense Tracker</h1>" in response.text


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
