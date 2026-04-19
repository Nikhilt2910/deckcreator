from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import EXCEL_DIR, OUTPUT_DIR, TEMPLATE_DIR
from app.core.presets import get_preset_template_path
from app.schemas.presentation import PresentationAnalysis
from app.services.analysis_service import analyze_data
from app.services.deck_prompt_service import build_prompt_only_deck_plan, research_theme_from_prompt
from app.services.excel_service import build_presentation_dataset, parse_excel_to_json
from app.services.ppt_service import generate_presentation
from app.services.reference_service import load_reference_context
from app.utils.file_manager import save_upload


EXCEL_EXTENSIONS = (".xlsx", ".xls", ".xlsm")
REFERENCE_EXTENSIONS = (".pptx", ".potx", ".pdf")


async def generate_report_from_uploads(
    excel_file: UploadFile | None,
    reference_file: UploadFile | None,
    built_in_template: str | None = None,
    prompt: str | None = None,
) -> Path:
    saved_excel: dict[str, Path | str] | None = None
    workbook_payload: dict | None = None
    presentation_dataset: dict | None = None

    if excel_file and excel_file.filename:
        _validate_extension(excel_file.filename, EXCEL_EXTENSIONS, "Excel")

        excel_bytes = await excel_file.read()
        if not excel_bytes:
            raise HTTPException(status_code=400, detail="The Excel file is empty.")

        saved_excel = save_upload(excel_file.filename, excel_bytes, EXCEL_DIR)
        workbook_payload = parse_excel_to_json(excel_bytes, saved_excel["name"])
        presentation_dataset = build_presentation_dataset(excel_bytes)

    saved_reference = await _resolve_reference_source(reference_file, built_in_template)
    reference_path = saved_reference["path"] if saved_reference else None
    reference_context = load_reference_context(reference_path)

    if workbook_payload is not None and presentation_dataset is not None:
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
            title=_build_report_title(str(saved_excel["name"])),
            executive_summary=analysis_result["executive_summary"],
            key_insights=analysis_result["key_insights"],
            trends=analysis_result["trends"],
            risks=analysis_result["risks"],
            kpis=presentation_dataset["kpis"],
            channel_rows=presentation_dataset["channel_rows"],
            region_rows=presentation_dataset["region_rows"],
            top_campaign_rows=presentation_dataset["top_campaign_rows"],
            sample_rows=presentation_dataset["sample_rows"],
            theme=research_theme_from_prompt(prompt) if reference_path is None and prompt and prompt.strip() else None,
        )
    else:
        if not prompt or not prompt.strip():
            raise HTTPException(
                status_code=400,
                detail="Add a prompt when generating a deck without an Excel workbook.",
            )

        try:
            prompt_plan = build_prompt_only_deck_plan(prompt, reference_context=reference_context)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Prompt-based deck generation failed: {exc}") from exc

        presentation_analysis = PresentationAnalysis(**prompt_plan.model_dump())

    return generate_presentation(
        reference_path=reference_path,
        analysis=presentation_analysis,
        output_dir=OUTPUT_DIR,
    )


def _build_report_title(file_name: str) -> str:
    return f"{Path(file_name).stem.replace('-', ' ').title()} Report"


async def _resolve_reference_source(
    reference_file: UploadFile | None,
    built_in_template: str | None,
) -> dict[str, Path | str] | None:
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

    return None


def _validate_extension(file_name: str | None, allowed_extensions: tuple[str, ...], label: str) -> None:
    if not file_name or not file_name.lower().endswith(allowed_extensions):
        extensions = ", ".join(allowed_extensions)
        raise HTTPException(status_code=400, detail=f"{label} must be one of: {extensions}.")
