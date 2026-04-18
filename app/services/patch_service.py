import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from app.schemas.ticket import TicketReviewOutcome


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def apply_unified_diff(patch_text: str) -> TicketReviewOutcome:
    git_path = _resolve_git_executable()
    if not git_path:
        return TicketReviewOutcome(
            applied=False,
            message="git is not installed, so the patch could not be applied automatically.",
            applied_at=datetime.now(timezone.utc),
        )

    if not patch_text.strip():
        return TicketReviewOutcome(
            applied=False,
            message="No patch content was available to apply.",
            applied_at=datetime.now(timezone.utc),
        )

    is_valid, validation_message = validate_unified_diff(patch_text)
    if not is_valid:
        return TicketReviewOutcome(
            applied=False,
            message=validation_message,
            applied_at=datetime.now(timezone.utc),
        )

    with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as handle:
        handle.write(patch_text)
        patch_path = Path(handle.name)

    try:
        result = subprocess.run(
            [git_path, "apply", "--reject", "--whitespace=fix", str(patch_path)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        patch_path.unlink(missing_ok=True)

    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
    if result.returncode == 0:
        return TicketReviewOutcome(
            applied=True,
            message=output or "Patch applied successfully.",
            applied_at=datetime.now(timezone.utc),
        )

    return TicketReviewOutcome(
        applied=False,
        message=output or "git apply failed.",
        applied_at=datetime.now(timezone.utc),
    )


def _resolve_git_executable() -> str | None:
    configured = os.getenv("GIT_EXECUTABLE")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("git")


def validate_unified_diff(patch_text: str) -> tuple[bool, str]:
    git_path = _resolve_git_executable()
    if not git_path:
        return False, "git is not installed, so the patch could not be applied automatically."

    if not patch_text.strip():
        return False, "No patch content was available to apply."

    if _looks_like_placeholder_patch(patch_text):
        return False, "The generated patch was only a placeholder diff and could not be applied automatically."

    with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False, encoding="utf-8") as handle:
        handle.write(patch_text)
        patch_path = Path(handle.name)

    try:
        result = subprocess.run(
            [git_path, "apply", "--check", "--verbose", str(patch_path)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        patch_path.unlink(missing_ok=True)

    if result.returncode == 0:
        return True, "Patch is valid."

    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
    return False, output or "git apply check failed."


def _looks_like_placeholder_patch(patch_text: str) -> bool:
    stripped = patch_text.strip()
    return "@@ ... @@" in stripped or "@@ ...@@" in stripped
