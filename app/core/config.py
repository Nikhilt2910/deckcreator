from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
EXCEL_DIR = UPLOADS_DIR / "excel"
TEMPLATE_DIR = UPLOADS_DIR / "templates"
OUTPUT_DIR = DATA_DIR / "output"
TICKETS_FILE = DATA_DIR / "tickets.json"


for directory in (DATA_DIR, UPLOADS_DIR, EXCEL_DIR, TEMPLATE_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
