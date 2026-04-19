from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, presentations, reports, tickets, uploads
from backend.app.api import approval, ticket, upload
from backend.app.core.config import FRONTEND_ORIGIN_REGEX, FRONTEND_ORIGINS


BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="DeckCreator Full Stack API",
    description="FastAPI backend for uploads, report generation, tickets, and approvals.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_origin_regex=FRONTEND_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Existing routes remain available.
app.include_router(health.router)
app.include_router(uploads.router)
app.include_router(presentations.router)
app.include_router(reports.router)
app.include_router(tickets.router)

# New API aliases for the frontend.
app.include_router(upload.router)
app.include_router(ticket.router)
app.include_router(approval.router)
