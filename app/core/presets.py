from pathlib import Path

from app.core.config import BASE_DIR


PRESET_DIR = BASE_DIR / "data" / "presets"

PRESET_TEMPLATES = [
    {
        "id": "case-study",
        "name": "Case Study",
        "description": "Narrative business case format with structured placeholders.",
        "file_name": "case-study.pptx",
    },
    {
        "id": "marketing-report",
        "name": "Marketing Report",
        "description": "Clean business report layout for KPI and channel performance decks.",
        "file_name": "marketing-report.pptx",
    },
    {
        "id": "photo-story",
        "name": "Photo Story",
        "description": "Visual storytelling deck with stronger image treatment.",
        "file_name": "photo-story.pptx",
    },
]


def list_preset_templates() -> list[dict[str, str]]:
    return PRESET_TEMPLATES


def get_preset_template_path(template_id: str) -> Path | None:
    for preset in PRESET_TEMPLATES:
        if preset["id"] == template_id:
            return PRESET_DIR / preset["file_name"]
    return None
