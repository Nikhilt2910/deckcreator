import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from app.schemas.ticket import TicketResolution


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CODEBASE_ROOTS = (
    BASE_DIR / "app",
    BASE_DIR / "templates",
    BASE_DIR / "static",
    BASE_DIR / "tests",
)
TOP_LEVEL_FILES = (
    BASE_DIR / "requirements.txt",
    BASE_DIR / "README.md",
)
ALLOWED_SUFFIXES = {".py", ".html", ".css", ".md", ".txt"}
MAX_FILE_CHARS = 4_000
MAX_TOTAL_CHARS = 40_000

ENGINEERING_PROMPT = """You are a senior engineer.

Given:
- a ticket description
- the current codebase

Do:
1. Identify files to change
2. Explain reasoning
3. Generate code changes

Output:
- list of files
- diff-style patch
- explanation

Rules:
- Be specific to the provided codebase.
- Prefer minimal, coherent changes over broad rewrites.
- Reference real file paths from the repository.
- The patch must be unified diff style and plausible for the provided files.
- If the ticket is ambiguous, state the assumption in the explanation and still provide the best patch you can.
"""


class EngineeringResolutionPayload(BaseModel):
    files: list[str] = Field(default_factory=list)
    patch: str
    explanation: str


def generate_ticket_resolution(ticket_description: str) -> TicketResolution:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_ENGINEERING_MODEL", "gpt-4.1")
    codebase_snapshot = _build_codebase_snapshot()

    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": ENGINEERING_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Ticket description:\n{ticket_description}\n\n"
                    f"Current codebase snapshot:\n{codebase_snapshot}"
                ),
            },
        ],
        text_format=EngineeringResolutionPayload,
    )

    if response.output_parsed is None:
        raise ValueError("OpenAI returned no engineering resolution.")

    payload = response.output_parsed
    return TicketResolution(
        files=payload.files,
        patch=payload.patch,
        explanation=payload.explanation,
        generated_at=datetime.now(timezone.utc),
    )


def _build_codebase_snapshot() -> str:
    sections: list[str] = []
    total_chars = 0

    for file_path in _iter_codebase_files():
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            continue
        excerpt = content[:MAX_FILE_CHARS]
        relative_path = file_path.relative_to(BASE_DIR).as_posix()
        section = f"FILE: {relative_path}\n```\n{excerpt}\n```"
        projected_size = total_chars + len(section)
        if projected_size > MAX_TOTAL_CHARS:
            break
        sections.append(section)
        total_chars = projected_size

    if not sections:
        return "Codebase snapshot unavailable."
    return "\n\n".join(sections)


def _iter_codebase_files() -> list[Path]:
    files: list[Path] = []
    for root in CODEBASE_ROOTS:
        if not root.exists():
            continue
        for file_path in sorted(root.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_SUFFIXES:
                files.append(file_path)
    for file_path in TOP_LEVEL_FILES:
        if file_path.exists():
            files.append(file_path)
    return files
