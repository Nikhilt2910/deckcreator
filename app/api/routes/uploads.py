from fastapi import APIRouter, File, UploadFile

from app.schemas.upload import UploadResponse
from app.services.upload_service import save_uploaded_files


router = APIRouter(tags=["uploads"])


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    excel_file: UploadFile = File(...),
    reference_file: UploadFile = File(...),
) -> UploadResponse:
    return await save_uploaded_files(excel_file=excel_file, reference_file=reference_file)
