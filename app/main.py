from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, presentations, reports, tickets, uploads


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="Excel To PowerPoint API",
    description="Upload Excel workbooks and PowerPoint templates for local processing.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(health.router)
app.include_router(uploads.router)
app.include_router(presentations.router)
app.include_router(reports.router)
app.include_router(tickets.router)
