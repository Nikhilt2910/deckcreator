import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from app.schemas.ticket import TicketAutomationResult


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def run_post_approval_pipeline(ticket_id: str, files_to_stage: list[str] | None = None) -> TicketAutomationResult:
    git_path = _resolve_git_executable()
    if not git_path:
        return TicketAutomationResult(
            message="git is not installed or configured, so commit/push could not run.",
            completed_at=datetime.now(timezone.utc),
        )

    test_result = _run_tests()
    if test_result.returncode != 0:
        return TicketAutomationResult(
            patch_applied=True,
            tests_passed=False,
            message=_combine_output("Tests failed.", test_result),
            completed_at=datetime.now(timezone.utc),
        )

    branch_name = os.getenv("GITHUB_BRANCH") or _current_branch(git_path) or "master"

    add_targets = files_to_stage or ["."]
    add_result = _run_command([git_path, "add", *add_targets])
    if add_result.returncode != 0:
        return TicketAutomationResult(
            patch_applied=True,
            tests_passed=True,
            branch=branch_name,
            message=_combine_output("Failed to stage changes.", add_result),
            completed_at=datetime.now(timezone.utc),
        )

    commit_result = _run_command([git_path, "commit", "-m", f"Apply approved ticket {ticket_id}"])
    if commit_result.returncode != 0:
        return TicketAutomationResult(
            patch_applied=True,
            tests_passed=True,
            branch=branch_name,
            message=_combine_output("Failed to create commit.", commit_result),
            completed_at=datetime.now(timezone.utc),
        )

    commit_sha_result = _run_command([git_path, "rev-parse", "HEAD"])
    commit_sha = commit_sha_result.stdout.strip() if commit_sha_result.returncode == 0 else None

    remote_url = os.getenv("GITHUB_REPO_URL")
    if remote_url:
        _ensure_remote(git_path, remote_url)

    push_result = _run_command([git_path, "push", "-u", "origin", branch_name])
    if push_result.returncode != 0:
        return TicketAutomationResult(
            patch_applied=True,
            tests_passed=True,
            pushed=False,
            branch=branch_name,
            commit_sha=commit_sha,
            message=_combine_output("Commit created but push failed.", push_result),
            completed_at=datetime.now(timezone.utc),
        )

    return TicketAutomationResult(
        patch_applied=True,
        tests_passed=True,
        pushed=True,
        branch=branch_name,
        commit_sha=commit_sha,
        message="Patch applied, tests passed, and changes were pushed to GitHub.",
        completed_at=datetime.now(timezone.utc),
    )


def _run_tests() -> subprocess.CompletedProcess[str]:
    python_executable = os.getenv("PYTHON_EXECUTABLE") or str(BASE_DIR / ".venv" / "Scripts" / "python.exe")
    return _run_command([python_executable, "-m", "unittest", "tests.test_upload"], timeout=180)


def _resolve_git_executable() -> str | None:
    configured = os.getenv("GIT_EXECUTABLE")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("git")


def _ensure_remote(git_path: str, remote_url: str) -> None:
    remote_check = _run_command([git_path, "remote", "get-url", "origin"])
    if remote_check.returncode == 0:
        current = remote_check.stdout.strip()
        if current != remote_url:
            _run_command([git_path, "remote", "set-url", "origin", remote_url])
        return
    _run_command([git_path, "remote", "add", "origin", remote_url])


def _current_branch(git_path: str) -> str | None:
    result = _run_command([git_path, "branch", "--show-current"])
    if result.returncode != 0:
        return None
    branch_name = result.stdout.strip()
    return branch_name or None


def _run_command(command: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _combine_output(prefix: str, result: subprocess.CompletedProcess[str]) -> str:
    details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
    if details:
        return f"{prefix}\n{details}"
    return prefix
