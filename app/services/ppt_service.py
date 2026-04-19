import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from app.schemas.presentation import PresentationAnalysis
from app.services.ppt_template_service import generate_template_preserving_presentation


BASE_DIR = Path(__file__).resolve().parent.parent.parent
RENDERER_DIR = BASE_DIR / "deck_renderer"
RENDERER_SCRIPT = RENDERER_DIR / "generateDeck.js"


def generate_presentation(reference_path: Path, analysis: PresentationAnalysis, output_dir: Path) -> Path:
    if reference_path.suffix.lower() in {".pptx", ".potx"}:
        return generate_template_preserving_presentation(
            reference_path=reference_path,
            analysis=analysis,
            output_dir=output_dir,
        )

    output_path = output_dir / _build_output_name(analysis.title)
    payload = {
        "analysis": analysis.model_dump(mode="json"),
        "referencePath": str(reference_path),
        "outputPath": str(output_path),
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
        temp_payload_path = Path(handle.name)

    try:
        _run_renderer(temp_payload_path)
    finally:
        temp_payload_path.unlink(missing_ok=True)

    if not output_path.exists():
        raise RuntimeError("The JavaScript deck renderer completed without creating an output file.")
    return output_path


def _run_renderer(payload_path: Path) -> None:
    node_path = _resolve_node_executable()
    if not node_path:
        raise RuntimeError("Node.js is not installed or configured, so deck generation cannot run.")
    if not RENDERER_SCRIPT.exists():
        raise RuntimeError("The JavaScript deck renderer was not found.")

    process = subprocess.run(
        [node_path, str(RENDERER_SCRIPT), str(payload_path)],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
        env=_build_renderer_env(),
        timeout=180,
    )

    if process.returncode != 0:
        details = "\n".join(part for part in (process.stdout.strip(), process.stderr.strip()) if part).strip()
        raise RuntimeError(f"PptxGenJS deck generation failed.\n{details}".strip())


def _build_renderer_env() -> dict[str, str]:
    env = os.environ.copy()
    node_dir = Path(_resolve_node_executable()).parent if _resolve_node_executable() else None
    if node_dir:
        env["PATH"] = f"{node_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def _resolve_node_executable() -> str | None:
    configured = os.getenv("NODE_EXECUTABLE")
    if configured and Path(configured).exists():
        return configured

    common_paths = (
        Path("C:/Program Files/nodejs/node.exe"),
        Path("C:/Program Files (x86)/nodejs/node.exe"),
    )
    for candidate in common_paths:
        if candidate.exists():
            return str(candidate)

    return shutil.which("node")


def _build_output_name(title: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in title).strip("-")
    suffix = uuid4().hex[:8]
    return f"{slug[:60]}-{suffix}.pptx"
