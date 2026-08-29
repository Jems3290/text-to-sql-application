import shutil
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from backend.database.validator import validate_uploaded_database


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_database(file: UploadFile) -> dict:
    original_filename = Path(file.filename or "database.db").name
    file_extension = Path(original_filename).suffix.lower()

    upload_id = str(uuid4())
    stored_filename = f"{upload_id}{file_extension}"
    stored_path = UPLOAD_DIR / stored_filename

    try:
        with stored_path.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)

        validate_uploaded_database(
            file_path=stored_path,
            original_filename=original_filename
        )

    except Exception:
        if stored_path.exists():
            stored_path.unlink()

        raise

    finally:
        file.file.close()

    return {
        "upload_id": upload_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "stored_path": str(stored_path)
    }