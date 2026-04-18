from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.services.presentation_service import create_downloadable_presentation


router = APIRouter(tags=["presentations"])


@router.post("/presentations/generate")
async def generate_presentation(
    ppt_template: UploadFile = File(...),
    analysis_json: str = Form(...),
) -> FileResponse:
    presentation_path = await create_downloadable_presentation(
        ppt_template=ppt_template,
        analysis_json=analysis_json,
    )
    return FileResponse(
        path=presentation_path,
        filename=presentation_path.name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
