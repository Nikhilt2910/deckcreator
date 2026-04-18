import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.ticket import TicketReviewOutcome


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def apply_unified_diff(patch_text: str) -> TicketReviewOutcome:
    git_path = shutil.which("git")
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
