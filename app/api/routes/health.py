from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.presets import list_preset_templates


router = APIRouter(tags=["health"])
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "app_name": "Excel To PowerPoint API",
            "upload_url": "/upload",
            "report_url": "/reports/generate",
            "preset_templates": list_preset_templates(),
            "health_url": "/health",
            "docs_url": "/docs",
        },
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
