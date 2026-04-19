from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import EXCEL_DIR, OUTPUT_DIR, TEMPLATE_DIR
from app.core.presets import get_preset_template_path
from app.schemas.presentation import PresentationAnalysis
from app.services.analysis_service import analyze_data
from app.services.excel_service import build_presentation_dataset, parse_excel_to_json
from app.services.ppt_service import generate_presentation
from app.services.reference_service import load_reference_context
from app.utils.file_manager import save_upload


EXCEL_EXTENSIONS = (".xlsx", ".xls", ".xlsm")
REFERENCE_EXTENSIONS = (".pptx", ".potx", ".pdf")


async def generate_report_from_uploads(
    excel_file: UploadFile,
    reference_file: UploadFile | None,
    built_in_template: str | None = None,
    prompt: str | None = None,
) -> Path:
    _validate_extension(excel_file.filename, EXCEL_EXTENSIONS, "Excel")

    excel_bytes = await excel_file.read()
    if not excel_bytes:
        raise HTTPException(status_code=400, detail="The Excel file is empty.")

    saved_excel = save_upload(excel_file.filename, excel_bytes, EXCEL_DIR)
    saved_reference = await _resolve_reference_source(reference_file, built_in_template)

    workbook_payload = parse_excel_to_json(excel_bytes, saved_excel["name"])
    presentation_dataset = build_presentation_dataset(excel_bytes)
    reference_context = load_reference_context(saved_reference["path"])

    try:
        analysis_result = analyze_data(
            {
                "workbook": workbook_payload,
                "presentation_dataset": presentation_dataset,
                "reference_context": reference_context,
            },
            deck_prompt=prompt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI analysis failed: {exc}") from exc

    presentation_analysis = PresentationAnalysis(
        title=_build_report_title(saved_excel["name"]),
        executive_summary=analysis_result["executive_summary"],
        key_insights=analysis_result["key_insights"],
        trends=analysis_result["trends"],
        risks=analysis_result["risks"],
        kpis=presentation_dataset["kpis"],
        channel_rows=presentation_dataset["channel_rows"],
        region_rows=presentation_dataset["region_rows"],
        top_campaign_rows=presentation_dataset["top_campaign_rows"],
        sample_rows=presentation_dataset["sample_rows"],
    )

    return generate_presentation(
        reference_path=saved_reference["path"],
        analysis=presentation_analysis,
        output_dir=OUTPUT_DIR,
    )


def _build_report_title(file_name: str) -> str:
    return f"{Path(file_name).stem.replace('-', ' ').title()} Report"


async def _resolve_reference_source(reference_file: UploadFile | None, built_in_template: str | None) -> dict[str, Path | str]:
    if reference_file and reference_file.filename:
        _validate_extension(reference_file.filename, REFERENCE_EXTENSIONS, "Reference file")
        reference_bytes = await reference_file.read()
        if not reference_bytes:
            raise HTTPException(status_code=400, detail="The reference file is empty.")
        return save_upload(reference_file.filename, reference_bytes, TEMPLATE_DIR)

    if built_in_template:
        preset_path = get_preset_template_path(built_in_template)
        if preset_path is None or not preset_path.exists():
            raise HTTPException(status_code=400, detail="Selected preset template was not found.")
        return {"name": preset_path.name, "path": preset_path}

    raise HTTPException(status_code=400, detail="Upload a reference file or choose a preset template.")


def _validate_extension(file_name: str | None, allowed_extensions: tuple[str, ...], label: str) -> None:
    if not file_name or not file_name.lower().endswith(allowed_extensions):
        extensions = ", ".join(allowed_extensions)
        raise HTTPException(status_code=400, detail=f"{label} must be one of: {extensions}.")
