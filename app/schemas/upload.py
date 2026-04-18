from pydantic import BaseModel


class UploadedFile(BaseModel):
    original_name: str
    saved_name: str
    saved_path: str


class UploadResponse(BaseModel):
    message: str
    excel_file: UploadedFile
    reference_file: UploadedFile
