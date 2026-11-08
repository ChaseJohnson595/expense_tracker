from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from expense_tracker.storage import get_database_path

app = FastAPI(title="Expense Tracker")
app.state.database_path = str(get_database_path())
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )
