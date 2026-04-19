import os
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _resolve_data_dir() -> Path:
    configured_root = os.getenv("APP_DATA_ROOT")
    if configured_root:
        return Path(configured_root)
    if os.getenv("VERCEL"):
        return Path(tempfile.gettempdir()) / "deckcreator-data"
    return BASE_DIR / "data"


DATA_DIR = _resolve_data_dir()
UPLOADS_DIR = DATA_DIR / "uploads"
EXCEL_DIR = UPLOADS_DIR / "excel"
TEMPLATE_DIR = UPLOADS_DIR / "templates"
OUTPUT_DIR = DATA_DIR / "output"
TICKETS_FILE = DATA_DIR / "tickets.json"


for directory in (DATA_DIR, UPLOADS_DIR, EXCEL_DIR, TEMPLATE_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
