import os
import re
from difflib import unified_diff
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from app.schemas.ticket import TicketResolution
from app.services.patch_service import validate_unified_diff


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CODEBASE_ROOTS = (
    BASE_DIR / "frontend",
    BASE_DIR / "backend",
    BASE_DIR / "app",
    BASE_DIR / "templates",
    BASE_DIR / "static",
    BASE_DIR / "tests",
)
TOP_LEVEL_FILES = (
    BASE_DIR / "requirements.txt",
    BASE_DIR / "README.md",
)
ALLOWED_SUFFIXES = {".py", ".html", ".css", ".md", ".txt", ".ts", ".tsx", ".js", ".jsx"}
MAX_FILE_CHARS = 4_000
MAX_TOTAL_CHARS = 40_000
IGNORED_PARTS = {"__pycache__", ".next", "node_modules", ".git", ".venv"}

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
- The patch must be a real unified diff that `git apply` can apply directly.
- Do not use placeholder hunks such as `@@ ... @@`, `existing code here`, or ellipses.
- Only edit lines that exist in the provided file contents.
- Include exact hunk headers and exact surrounding context from the provided files.
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

    literal_resolution = _try_generate_literal_text_resolution(ticket_description)
    if literal_resolution is not None:
        return literal_resolution

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_ENGINEERING_MODEL", "gpt-5.2-codex")
    codebase_snapshot = _build_codebase_snapshot()
    validation_error = ""
    previous_files: list[str] = []

    for attempt in range(2):
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": ENGINEERING_PROMPT},
                {
                    "role": "user",
                    "content": _build_generation_prompt(
                        ticket_description=ticket_description,
                        codebase_snapshot=codebase_snapshot,
                        validation_error=validation_error,
                    ),
                },
            ],
            text_format=EngineeringResolutionPayload,
        )

        if response.output_parsed is None:
            raise ValueError("OpenAI returned no engineering resolution.")

        payload = response.output_parsed
        is_valid, message = validate_unified_diff(payload.patch)
        if is_valid:
            return TicketResolution(
                files=payload.files,
                patch=payload.patch,
                explanation=payload.explanation,
                generated_at=datetime.now(timezone.utc),
            )

        validation_error = message
        previous_files = payload.files
        targeted_snapshot = _build_targeted_snapshot(previous_files)
        if targeted_snapshot:
            codebase_snapshot = targeted_snapshot

    raise ValueError(f"OpenAI returned a non-applyable engineering resolution: {validation_error}")


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


def _build_targeted_snapshot(files: list[str]) -> str:
    sections: list[str] = []
    total_chars = 0

    for relative_name in files:
        normalized = relative_name.replace("\\", "/").strip("/")
        file_path = BASE_DIR / normalized
        if not file_path.exists() or not file_path.is_file():
            continue
        if any(part in IGNORED_PARTS for part in file_path.parts):
            continue
        if file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            continue
        excerpt = content[:MAX_FILE_CHARS]
        section = f"FILE: {normalized}\n```\n{excerpt}\n```"
        projected_size = total_chars + len(section)
        if projected_size > MAX_TOTAL_CHARS:
            break
        sections.append(section)
        total_chars = projected_size

    return "\n\n".join(sections)


def _build_generation_prompt(
    ticket_description: str,
    codebase_snapshot: str,
    validation_error: str,
) -> str:
    retry_note = ""
    if validation_error:
        retry_note = (
            "The previous patch was invalid and failed automated validation.\n"
            f"Validation error:\n{validation_error}\n\n"
            "Regenerate the patch with exact file context and real applyable hunks only.\n\n"
        )
    return (
        f"Ticket description:\n{ticket_description}\n\n"
        f"{retry_note}"
        "Current codebase snapshot:\n"
        f"{codebase_snapshot}"
    )


def _iter_codebase_files() -> list[Path]:
    files: list[Path] = []
    for root in CODEBASE_ROOTS:
        if not root.exists():
            continue
        for file_path in sorted(root.rglob("*")):
            if any(part in IGNORED_PARTS for part in file_path.parts):
                continue
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_SUFFIXES:
                files.append(file_path)
    for file_path in TOP_LEVEL_FILES:
        if file_path.exists():
            files.append(file_path)
    return files


def _try_generate_literal_text_resolution(ticket_description: str) -> TicketResolution | None:
    normalized = ticket_description.lower()
    block_resolution = _try_generate_named_block_resolution(ticket_description)
    if block_resolution is not None:
        return block_resolution

    additive_resolution = _try_generate_literal_addition_resolution(ticket_description)
    if additive_resolution is not None:
        return additive_resolution

    if not any(keyword in normalized for keyword in ("remove", "delete", "hide")):
        return None

    target_text = _extract_literal_target(ticket_description)
    if not target_text:
        return None
    candidates: list[tuple[Path, str, str]] = []
    for file_path in _iter_codebase_files():
        if "tests" in file_path.parts:
            continue
        original = _read_file_preserving_newlines(file_path)
        if target_text not in original and target_text.lower() not in original.lower():
            continue
        updated = _remove_literal_occurrences(original, target_text)
        if updated == original:
            continue
        candidates.append((file_path, original, updated))

    candidate = _select_literal_candidate(candidates, ticket_description)
    if candidate is None:
        return None

    file_path, original, updated = candidate
    relative_path = file_path.relative_to(BASE_DIR).as_posix()
    patch = "".join(
        unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
    )

    is_valid, _ = validate_unified_diff(patch)
    if not is_valid:
        return None

    return TicketResolution(
        files=[relative_path],
        patch=patch,
        explanation=(
            f'The ticket requests removing the exact text "{target_text}". '
            f'That text was found uniquely in `{relative_path}`, so the resolution removes it directly from that file.'
        ),
        generated_at=datetime.now(timezone.utc),
    )


def _try_generate_literal_addition_resolution(ticket_description: str) -> TicketResolution | None:
    normalized = ticket_description.lower()
    if not any(keyword in normalized for keyword in ("add", "include", "mention", "show")):
        return None

    target_text = _extract_literal_target(ticket_description)
    if not target_text:
        return None

    if "inputs" in normalized and "reference file" in normalized:
        return _try_generate_reference_file_addition_resolution(target_text)

    return None


def _read_file_preserving_newlines(file_path: Path) -> str:
    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        return handle.read()


def _select_literal_candidate(
    candidates: list[tuple[Path, str, str]],
    ticket_description: str,
) -> tuple[Path, str, str] | None:
    if len(candidates) == 1:
        return candidates[0]

    normalized = ticket_description.lower()
    route_preference = _preferred_frontend_route(normalized)
    if route_preference is not None:
        route_matches = [
            candidate for candidate in candidates if route_preference in candidate[0].as_posix().lower()
        ]
        if len(route_matches) == 1:
            return route_matches[0]

    ui_keywords = ("ui", "page", "screen", "section", "block", "button", "text", "label")
    if any(keyword in normalized for keyword in ui_keywords):
        frontend_candidates = [candidate for candidate in candidates if "frontend" in candidate[0].parts]
        if len(frontend_candidates) == 1:
            return frontend_candidates[0]

        template_candidates = [candidate for candidate in candidates if "templates" in candidate[0].parts]
        if len(template_candidates) == 1:
            return template_candidates[0]

    return None


def _preferred_frontend_route(normalized_description: str) -> str | None:
    route_keywords = {
        "frontend/app/tickets/": ("ticket", "tickets", "support", "feedback"),
        "frontend/app/upload/": ("upload", "reference file", "inputs", "deck"),
        "frontend/app/status/": ("status", "tracking", "track"),
        "frontend/app/review/": ("review", "approve", "reject"),
    }
    for route, keywords in route_keywords.items():
        if any(keyword in normalized_description for keyword in keywords):
            return route
    return None


def _remove_literal_occurrences(source_text: str, target_text: str) -> str:
    updated = source_text
    patterns = [
        rf",\s*`?\.?{re.escape(target_text)}`?",
        rf"`?\.?{re.escape(target_text)}`?\s*,\s*",
        rf"`?{re.escape(target_text)}`?",
    ]
    for pattern in patterns:
        updated = re.sub(pattern, "", updated)
    if updated == source_text:
        patterns_ci = [
            rf",\s*`?\.?{re.escape(target_text)}`?",
            rf"`?\.?{re.escape(target_text)}`?\s*,\s*",
            rf"`?{re.escape(target_text)}`?",
        ]
        for pattern in patterns_ci:
            updated = re.sub(pattern, "", updated, flags=re.IGNORECASE)
    return updated


def _try_generate_reference_file_addition_resolution(target_text: str) -> TicketResolution | None:
    file_path = BASE_DIR / "templates" / "index.html"
    if not file_path.exists():
        return None

    original = _read_file_preserving_newlines(file_path)
    updated = original
    normalized_token = target_text.lstrip(".").lower()
    display_token = f"`.{normalized_token}`"
    accept_token = f".{normalized_token}"

    updated = re.sub(
        r"Reference file:\s+([^<]+)</li>",
        lambda match: _insert_display_token(match.group(1), display_token),
        updated,
        count=1,
    )
    updated = re.sub(
        r'accept="([^"]+)"',
        lambda match: _insert_accept_token(match.group(1), accept_token),
        updated,
        count=1,
    )

    if updated == original:
        return None

    relative_path = file_path.relative_to(BASE_DIR).as_posix()
    patch = "".join(
        unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
    )
    is_valid, _ = validate_unified_diff(patch)
    if not is_valid:
        return None

    return TicketResolution(
        files=[relative_path],
        patch=patch,
        explanation=(
            f'The ticket requests adding "{target_text}" back to the Reference File options in the Inputs block. '
            f'The resolver updates both the visible text and the file input accept list in `{relative_path}`.'
        ),
        generated_at=datetime.now(timezone.utc),
    )


def _extract_literal_target(ticket_description: str) -> str | None:
    quoted_match = re.search(r'["\']([^"\']+)["\']', ticket_description)
    if quoted_match:
        return quoted_match.group(1).strip()

    unquoted_patterns = [
        r"\b(?:add|include|mention|show)\s+([a-zA-Z0-9._-]+)\s+files?\b",
        r"\b(?:add|include|mention|show)\s+([a-zA-Z0-9._-]+)\s+text\b",
        r"\b(?:add|include|mention|show)\s+([a-zA-Z0-9._-]+)\b",
        r"\bremove\s+([a-zA-Z0-9._-]+)\s+text\b",
        r"\bremove\s+([a-zA-Z0-9._-]+)\b",
        r"\bdelete\s+([a-zA-Z0-9._-]+)\s+text\b",
        r"\bdelete\s+([a-zA-Z0-9._-]+)\b",
        r"\bhide\s+([a-zA-Z0-9._-]+)\s+text\b",
        r"\bhide\s+([a-zA-Z0-9._-]+)\b",
    ]
    normalized = ticket_description.strip()
    for pattern in unquoted_patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" ,.:;")
    return None


def _try_generate_named_block_resolution(ticket_description: str) -> TicketResolution | None:
    normalized = ticket_description.lower()
    if not any(keyword in normalized for keyword in ("remove", "delete", "hide")):
        return None
    if not any(keyword in normalized for keyword in ("block", "section", "card", "panel")):
        return None

    target_text = _extract_literal_target(ticket_description)
    if not target_text:
        return None
    if len(target_text.strip()) < 4 or " " not in target_text.strip():
        return None

    candidates: list[tuple[Path, str, str]] = []
    for file_path in _iter_codebase_files():
        if "tests" in file_path.parts:
            continue
        original = _read_file_preserving_newlines(file_path)
        updated = _remove_named_block(
            source_text=original,
            target_text=target_text,
            ticket_description=ticket_description,
        )
        if updated == original:
            continue
        candidates.append((file_path, original, updated))

    candidate = _select_literal_candidate(candidates, ticket_description)
    if candidate is None and len(candidates) == 1:
        candidate = candidates[0]
    if candidate is None:
        return None

    file_path, original, updated = candidate
    relative_path = file_path.relative_to(BASE_DIR).as_posix()
    patch = "".join(
        unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
    )
    is_valid, _ = validate_unified_diff(patch)
    if not is_valid:
        return None

    return TicketResolution(
        files=[relative_path],
        patch=patch,
        explanation=(
            f'The ticket requests removing the UI block containing "{target_text}". '
            f'The resolver found that block in `{relative_path}` and removed the enclosing JSX/HTML section.'
        ),
        generated_at=datetime.now(timezone.utc),
    )


def _remove_named_block(source_text: str, target_text: str, ticket_description: str) -> str:
    lines = source_text.splitlines(keepends=True)
    lower_target = target_text.lower()
    normalized_description = ticket_description.lower()

    for index, line in enumerate(lines):
        if lower_target not in line.lower():
            continue

        start = _find_block_start(lines, index, normalized_description)
        if start is None:
            continue
        end = _find_block_end(lines, start)
        if end is None or end < start:
            continue

        updated_lines = lines[:start] + lines[end + 1 :]
        updated = "".join(updated_lines)
        if updated != source_text:
            return updated

    return source_text


def _find_block_start(lines: list[str], index: int, normalized_description: str) -> int | None:
    jsx_pattern = re.compile(r"^\s*<(section|aside|article|div)\b")
    scored_candidates: list[tuple[int, int]] = []

    for current in range(index, -1, -1):
        line = lines[current]
        if not jsx_pattern.search(line):
            continue
        if _is_single_line_container(line):
            continue

        end = _find_block_end(lines, current)
        if end is None or end < index:
            continue

        score = _score_block_candidate(
            line=line,
            start=current,
            end=end,
            normalized_description=normalized_description,
        )
        scored_candidates.append((score, current))

    if not scored_candidates:
        return None

    scored_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return scored_candidates[0][1]


def _is_single_line_container(line: str) -> bool:
    opening_tags = re.findall(r"<(section|aside|article|div)\b", line)
    if not opening_tags:
        return False
    tag = opening_tags[0]
    if re.search(rf"<{tag}\b[^>]+/>", line):
        return True
    return re.search(rf"</{tag}\s*>", line) is not None


def _score_block_candidate(
    line: str,
    start: int,
    end: int,
    normalized_description: str,
) -> int:
    lowered_line = line.lower()
    span = end - start + 1
    score = 0

    if "<aside" in lowered_line:
        score += 80
    elif "<section" in lowered_line:
        score += 40
    elif "<article" in lowered_line:
        score += 30
    elif "<div" in lowered_line:
        score += 15

    if "side-rail" in lowered_line:
        score += 120
    if "console-card" in lowered_line:
        score += 40
    if "signal-list" in lowered_line:
        score += 30

    if any(
        phrase in normalized_description
        for phrase in (
            "side-rail",
            "next to the request type",
            "next to request type",
            "ticket stored locally",
            "jira issue created",
            "resolution drafted",
            "developer review email sent when valid",
            "4 steps",
        )
    ):
        if "side-rail" in lowered_line:
            score += 200
        if "console-card" in lowered_line:
            score += 80

    if any(root_marker in lowered_line for root_marker in ("className=\"stack", "className=\"workspace", "className=\"page-hero")):
        score -= 120

    if span <= 2:
        score -= 80
    elif span <= 10:
        score += 20
    elif span <= 40:
        score += 10
    else:
        score -= 20

    return score


def _find_block_end(lines: list[str], start: int) -> int | None:
    depth = 0
    for current in range(start, len(lines)):
        opening = len(re.findall(r"<(section|aside|article|div)\b", lines[current]))
        closing = len(re.findall(r"</(section|aside|article|div)\b", lines[current]))
        self_closing = len(re.findall(r"<(section|aside|article|div)\b[^>]+/>", lines[current]))
        depth += opening - closing - self_closing
        if depth <= 0:
            return current
    return None


def _insert_display_token(existing_segment: str, display_token: str) -> str:
    if display_token in existing_segment:
        return f"Reference file: {existing_segment}</li>"
    parts = [part.strip() for part in existing_segment.split(",")]
    if "`.pdf`" in parts:
        index = parts.index("`.pdf`")
        parts.insert(index, display_token)
    else:
        parts.append(display_token)
    return f"Reference file: {', '.join(parts)}</li>"


def _insert_accept_token(existing_segment: str, accept_token: str) -> str:
    parts = [part.strip() for part in existing_segment.split(",") if part.strip()]
    if accept_token in parts:
        return f'accept="{existing_segment}"'
    if ".pdf" in parts:
        index = parts.index(".pdf")
        parts.insert(index, accept_token)
    else:
        parts.append(accept_token)
    return f'accept="{",".join(parts)}"'
