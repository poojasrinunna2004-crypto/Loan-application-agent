from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import database, service
from app.schemas import ApplicationDraft, SubmissionConfirmation


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize_database()
    yield


app = FastAPI(
    title="Mock Loan Application API",
    description="Training API backed only by fictional local data.",
    lifespan=lifespan,
)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock-only"}


@app.get("/customers")
def get_customers() -> list[dict[str, Any]]:
    return service.list_customers()


@app.post("/applications", status_code=201)
def create_application(draft: ApplicationDraft) -> dict[str, Any]:
    try:
        return service.create_draft(**draft.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/applications/{application_id}")
def get_application(application_id: int) -> dict[str, Any]:
    try:
        return service.get_application(application_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/applications/{application_id}/submit")
def submit_application(
    application_id: int, request: SubmissionConfirmation
) -> dict[str, Any]:
    try:
        return service.submit_application(application_id, request.confirmation)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
