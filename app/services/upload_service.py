from fastapi import HTTPException, UploadFile

from app.core.config import EXCEL_DIR, TEMPLATE_DIR
from app.schemas.upload import UploadResponse
from app.services.analysis_service import build_analysis_job_hint
from app.services.presentation_service import build_presentation_job_hint
from app.utils.file_manager import save_upload


EXCEL_EXTENSIONS = (".xlsx", ".xls", ".xlsm")
REFERENCE_EXTENSIONS = (".pptx", ".potx", ".pdf")


async def save_uploaded_files(excel_file: UploadFile, reference_file: UploadFile) -> UploadResponse:
    _validate_extension(excel_file.filename, EXCEL_EXTENSIONS, "Excel")
    _validate_extension(reference_file.filename, REFERENCE_EXTENSIONS, "Reference file")

    excel_bytes = await excel_file.read()
    template_bytes = await reference_file.read()

    if not excel_bytes:
        raise HTTPException(status_code=400, detail="The Excel file is empty.")
    if not template_bytes:
        raise HTTPException(status_code=400, detail="The reference file is empty.")

    saved_excel = save_upload(excel_file.filename, excel_bytes, EXCEL_DIR)
    saved_template = save_upload(reference_file.filename, template_bytes, TEMPLATE_DIR)

    # These placeholders define where later analysis and generation steps plug in.
    build_analysis_job_hint(saved_excel["path"])
    build_presentation_job_hint(saved_template["path"])

    return UploadResponse(
        message="Files uploaded successfully.",
        excel_file={
            "original_name": excel_file.filename,
            "saved_name": saved_excel["name"],
            "saved_path": str(saved_excel["path"]),
        },
        reference_file={
            "original_name": reference_file.filename,
            "saved_name": saved_template["name"],
            "saved_path": str(saved_template["path"]),
        },
    )


def _validate_extension(file_name: str | None, allowed_extensions: tuple[str, ...], label: str) -> None:
    if not file_name or not file_name.lower().endswith(allowed_extensions):
        extensions = ", ".join(allowed_extensions)
        raise HTTPException(status_code=400, detail=f"{label} must be one of: {extensions}.")
