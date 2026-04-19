from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.services.report_service import generate_report_from_uploads


router = APIRouter(tags=["reports"])


@router.post("/reports/generate")
async def generate_report(
    excel_file: UploadFile = File(...),
    reference_file: UploadFile | None = File(default=None),
    built_in_template: str | None = Form(default=None),
    prompt: str | None = Form(default=None),
) -> FileResponse:
    presentation_path = await generate_report_from_uploads(
        excel_file=excel_file,
        reference_file=reference_file,
        built_in_template=built_in_template,
        prompt=prompt,
    )
    return FileResponse(
        path=presentation_path,
        filename=presentation_path.name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
