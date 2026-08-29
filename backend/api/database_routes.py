from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.services.upload_service import save_uploaded_database


router = APIRouter(
    prefix="/database",
    tags=["Database"]
)


@router.post("/upload")
def upload_database(file: UploadFile = File(...)):
    try:
        upload_info = save_uploaded_database(file)

        return {
            "message": "Database uploaded and validated successfully.",
            "database": upload_info
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error