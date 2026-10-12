from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import database, service
from app.schemas import ApplicationDraft, SubmissionConfirmation


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize_database()
    yield


app = FastAPI(
    title="Loan Studio API",
    description=(
        "A mock training service using fictional customer records. No bank is contacted.\n\n"
        "**Suggested flow:** Choose a sample customer, create and review a draft, then submit "
        "only after explicit user confirmation."
    ),
    version="1.0.0",
    docs_url=None,
    redoc_url="/reference",
    openapi_tags=[
        {
            "name": "Getting started",
            "description": "Check the service and choose a fictional sample customer.",
        },
        {
            "name": "Loan applications",
            "description": "Create and review drafts. Submission requires explicit confirmation.",
        },
    ],
    lifespan=lifespan,
)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/docs", include_in_schema=False)
def api_guide() -> FileResponse:
    return FileResponse(STATIC_DIR / "docs.html")


@app.get("/swagger", include_in_schema=False)
def interactive_api_docs() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title="Interactive API | Loan Studio",
        swagger_css_url="/static/swagger.css",
        swagger_ui_parameters={
            "docExpansion": "list",
            "filter": True,
            "displayRequestDuration": True,
            "defaultModelsExpandDepth": -1,
            "tryItOutEnabled": True,
        },
    )


@app.get(
    "/health",
    tags=["Getting started"],
    summary="Check that the service is online",
    description="Returns the current health and confirms this is the mock environment.",
)
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock-only"}


@app.get(
    "/customers",
    tags=["Getting started"],
    summary="Choose a sample customer",
    description="Lists fictional training records. Use a customer's ID when creating a draft.",
)
def get_customers() -> list[dict[str, Any]]:
    return service.list_customers()


@app.post(
    "/applications",
    status_code=201,
    tags=["Loan applications"],
    summary="Save a loan application draft",
    description="Creates a draft only. This does not submit the application or contact a bank.",
)
def create_application(draft: ApplicationDraft) -> dict[str, Any]:
    try:
        return service.create_draft(**draft.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get(
    "/applications/{application_id}",
    tags=["Loan applications"],
    summary="Review a saved application",
    description="Returns the saved details and status. Reading an application never submits it.",
)
def get_application(application_id: int) -> dict[str, Any]:
    try:
        return service.get_application(application_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/applications/{application_id}/submit",
    tags=["Loan applications"],
    summary="Submit after explicit confirmation",
    description=(
        "Call this only after the user has reviewed the application and confirmed. "
        "The JSON field `confirmation` must be the boolean `true`. This updates mock data only."
    ),
)
def submit_application(
    application_id: int, request: SubmissionConfirmation
) -> dict[str, Any]:
    try:
        return service.submit_application(application_id, request.confirmation)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
