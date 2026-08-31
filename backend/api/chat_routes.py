import sqlite3
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.database.schema_builder import generate_schema_context
from backend.services.question_processor import process_user_question
from backend.services.ambiguity_detector import detect_question_ambiguity
from backend.services.relevance_detector import detect_question_relevance


class QuestionRequest(BaseModel):
    question: str

class RelevanceRequest(BaseModel):
    question: str
    database_path: str

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/process-question")
def process_question(request: QuestionRequest):
    try:
        processed_question = process_user_question(request.question)

        return {
            "message": "Question processed successfully.",
            "processed_question": processed_question
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


@router.post("/check-relevance")
def check_question_relevance(request: RelevanceRequest):
    database_path = Path(request.database_path)

    if not database_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Database file not found."
        )

    try:
        processed_question = process_user_question(request.question)

        schema_context_info = generate_schema_context(database_path)

        relevance_result = detect_question_relevance(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        return {
            "message": "Question relevance checked successfully.",
            "processed_question": processed_question,
            "relevance": relevance_result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail="Unable to analyze the uploaded database."
        ) from error


@router.post("/check-ambiguity")
def check_question_ambiguity(request: RelevanceRequest):
    database_path = Path(request.database_path)

    if not database_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Database file not found."
        )

    try:
        processed_question = process_user_question(request.question)

        schema_context_info = generate_schema_context(database_path)

        relevance_result = detect_question_relevance(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        if not relevance_result["is_relevant"]:
            return {
                "message": "Question is not relevant to the uploaded database.",
                "processed_question": processed_question,
                "relevance": relevance_result,
                "ambiguity": None
            }

        ambiguity_result = detect_question_ambiguity(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        return {
            "message": "Question ambiguity checked successfully.",
            "processed_question": processed_question,
            "relevance": relevance_result,
            "ambiguity": ambiguity_result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail="Unable to analyze the uploaded database."
        ) from error