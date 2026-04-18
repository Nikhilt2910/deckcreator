import json
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import OUTPUT_DIR, TEMPLATE_DIR
from app.schemas.presentation import PresentationAnalysis
from app.utils.file_manager import save_upload
from app.services.ppt_service import generate_presentation


PPT_EXTENSIONS = (".pptx", ".potx")


async def create_downloadable_presentation(ppt_template: UploadFile, analysis_json: str) -> Path:
    _validate_template(ppt_template.filename)

    template_bytes = await ppt_template.read()
    if not template_bytes:
        raise HTTPException(status_code=400, detail="The PowerPoint template is empty.")

    saved_template = save_upload(ppt_template.filename, template_bytes, TEMPLATE_DIR)
    analysis = _parse_analysis_json(analysis_json)

    return generate_presentation(
        reference_path=saved_template["path"],
        analysis=analysis,
        output_dir=OUTPUT_DIR,
    )


def build_presentation_job_hint(template_path: Path) -> dict[str, str]:
    return {
        "status": "ready",
        "next_step": "generate_presentation",
        "template_path": str(template_path),
    }


def _parse_analysis_json(analysis_json: str) -> PresentationAnalysis:
    try:
        payload = json.loads(analysis_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="analysis_json must be valid JSON.") from exc

    try:
        return PresentationAnalysis.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid analysis payload: {exc}") from exc


def _validate_template(file_name: str | None) -> None:
    if not file_name or not file_name.lower().endswith(PPT_EXTENSIONS):
        extensions = ", ".join(PPT_EXTENSIONS)
        raise HTTPException(status_code=400, detail=f"PowerPoint template must be one of: {extensions}.")
