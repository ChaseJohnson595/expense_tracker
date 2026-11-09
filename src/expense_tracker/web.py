from datetime import date
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from expense_tracker.models import Expense, create_expense, summarize_expenses
from expense_tracker.storage import (
    StorageError,
    add_expense,
    delete_expense,
    get_database_path,
    list_expenses,
    load_expenses,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

FORM_FIELDS = ("amount", "category", "date", "note")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/")
def home(request: Request) -> HTMLResponse:
    created = request.query_params.get("created") == "1"
    deleted = request.query_params.get("deleted") == "1"
    return _render_home(request, created=created, deleted=deleted)


@router.get("/expenses/{expense_id}/delete")
def confirm_delete_expense(request: Request, expense_id: str) -> HTMLResponse:
    try:
        expense = next(
            (
                item
                for item in load_expenses(request.app.state.database_path)
                if item.id == expense_id
            ),
            None,
        )
    except StorageError as error:
        return _render_home(
            request,
            error=f"Could not load expense: {error}",
            status_code=500,
        )
    if expense is None:
        return _render_home(request, error="Expense not found.", status_code=404)
    return _render_home(request, delete_confirmation=expense)


@router.post("/expenses/{expense_id}/delete")
def delete_expense_from_web(request: Request, expense_id: str) -> Response:
    try:
        deleted = delete_expense(expense_id, request.app.state.database_path)
    except StorageError as error:
        return _render_home(
            request,
            error=f"Could not delete expense: {error}",
            status_code=500,
        )
    if not deleted:
        return _render_home(request, error="Expense not found.", status_code=404)
    return RedirectResponse(url="/?deleted=1", status_code=303)


@router.post("/")
async def create_expense_from_form(
    request: Request,
) -> Response:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip()
    if content_type != "application/x-www-form-urlencoded":
        return _render_home(
            request, error="Unsupported form content type.", status_code=415
        )
    try:
        values = _parse_form_values(await request.body())
    except ValueError as error:
        return _render_home(request, error=str(error), status_code=400)
    try:
        expense = create_expense(
            values["amount"],
            values["category"],
            expense_date=values["date"] or None,
            note=values["note"] or None,
        )
    except (TypeError, ValueError) as error:
        return _render_home(request, form=values, error=str(error), status_code=400)

    try:
        add_expense(expense, request.app.state.database_path)
    except StorageError as error:
        return _render_home(
            request,
            form=values,
            error=f"Could not save expense: {error}",
            status_code=500,
        )
    return RedirectResponse(url="/?created=1", status_code=303)


def _parse_form_values(body: bytes) -> dict[str, str]:
    try:
        encoded_form = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("Form data must use UTF-8 encoding.") from error
    submitted = parse_qs(encoded_form, keep_blank_values=True, strict_parsing=True)
    values = {}
    for name in FORM_FIELDS:
        field_values = submitted.get(name, [])
        if len(field_values) > 1:
            raise ValueError(f"{name} must be submitted only once.")
        values[name] = field_values[0] if field_values else ""
    return values


def _render_home(
    request: Request,
    *,
    form: dict[str, str] | None = None,
    error: str | None = None,
    created: bool = False,
    deleted: bool = False,
    delete_confirmation: Expense | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    filters = {
        "start_date": request.query_params.get("start_date", ""),
        "end_date": request.query_params.get("end_date", ""),
        "category": request.query_params.get("category", ""),
    }
    try:
        expenses = list_expenses(
            request.app.state.database_path,
            start_date=filters["start_date"] or None,
            end_date=filters["end_date"] or None,
            category=filters["category"] or None,
        )
    except ValueError as list_error:
        error = str(list_error)
        status_code = 400
        expenses = []
    except StorageError as list_error:
        error = f"Could not load expenses: {list_error}"
        status_code = 500
        expenses = []

    current_month = date.today().strftime("%Y-%m")
    try:
        monthly_total_cents, category_totals = summarize_expenses(
            load_expenses(request.app.state.database_path), month=current_month
        )
    except StorageError as summary_error:
        error = f"Could not load monthly summary: {summary_error}"
        status_code = 500
        monthly_total_cents = None
        category_totals = {}

    form_values = form or {
        "amount": "",
        "category": "",
        "date": date.today().isoformat(),
        "note": "",
    }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "form": form_values,
            "error": error,
            "created": created,
            "deleted": deleted,
            "delete_confirmation": delete_confirmation,
            "filters": filters,
            "expenses": expenses,
            "current_month": current_month,
            "monthly_total_cents": monthly_total_cents,
            "category_totals": category_totals,
        },
        status_code=status_code,
    )


def create_app(database_path: Path | str | None = None) -> FastAPI:
    application = FastAPI(title="Expense Tracker")
    selected_path = get_database_path() if database_path is None else database_path
    application.state.database_path = str(selected_path)
    application.include_router(router)
    return application


app = create_app()
