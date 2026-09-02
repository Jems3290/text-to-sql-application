import sqlite3
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.services.upload_service import save_uploaded_database
from backend.database.schema_builder import generate_schema_context
from backend.database.schema_extractor import extract_database_schema
from backend.services.database_registry import register_database
from backend.database.relationship_analyzer import analyze_database_relationships

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


@router.get("/schema")
def get_database_schema(database_path: str):
    path = Path(database_path)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Database file not found."
        )

    try:
        schema = extract_database_schema(path)

        return {
            "message": "Database schema extracted successfully.",
            "schema": schema
        }

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract schema from the SQLite database."
        ) from error


@router.get("/relationships")
def get_database_relationships(database_path: str):
    path = Path(database_path)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Database file not found."
        )

    try:
        relationship_info = analyze_database_relationships(path)

        return {
            "message": "Database relationships analyzed successfully.",
            "relationship_info": relationship_info
        }

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail="Unable to analyze database relationships."
        ) from error


@router.get("/schema-context")
def get_schema_context(database_path: str):
    path = Path(database_path)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Database file not found."
        )

    try:
        schema_context_info = generate_schema_context(path)

        return {
            "message": "Schema context generated successfully.",
            "schema_context_info": schema_context_info
        }

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail="Unable to generate schema context."
        ) from error