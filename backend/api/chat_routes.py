import sqlite3
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.llm.prompts import build_text_to_sql_prompt
from backend.database.schema_builder import generate_schema_context
from backend.services.question_processor import process_user_question
from backend.llm.clarification_generator import generate_clarification
from backend.services.ambiguity_detector import detect_question_ambiguity
from backend.services.relevance_detector import detect_question_relevance
from backend.services.conversation_manager import (
    create_clarification_session,
    get_resolved_conversation_context,
    resolve_clarification
)


class QuestionRequest(BaseModel):
    question: str

class RelevanceRequest(BaseModel):
    question: str
    database_path: str

class ClarificationAnswerRequest(BaseModel):
    conversation_id: str
    answer: str

class ResolvedPromptRequest(BaseModel):
    conversation_id: str

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


@router.post("/generate-clarification")
def generate_question_clarification(request: RelevanceRequest):
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
                "ambiguity": None,
                "clarification": None
            }

        ambiguity_result = detect_question_ambiguity(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        if not ambiguity_result["is_ambiguous"]:
            return {
                "message": "Question is clear and does not require clarification.",
                "processed_question": processed_question,
                "relevance": relevance_result,
                "ambiguity": ambiguity_result,
                "clarification": None
            }

        clarification_result = generate_clarification(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"],
            ambiguity_result=ambiguity_result
        )

        conversation_id = create_clarification_session(
            original_question=processed_question["original_question"],
            normalized_question=processed_question["normalized_question"],
            database_path=str(database_path),
            schema_context=schema_context_info["schema_context"],
            ambiguity_result=ambiguity_result,
            clarification_result=clarification_result
        )

        return {
            "message": "Clarification generated successfully.",
            "conversation_id": conversation_id,
            "processed_question": processed_question,
            "relevance": relevance_result,
            "ambiguity": ambiguity_result,
            "clarification": clarification_result
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


@router.post("/submit-clarification")
def submit_clarification(request: ClarificationAnswerRequest):
    try:
        resolved_conversation = resolve_clarification(
            conversation_id=request.conversation_id,
            clarification_answer=request.answer
        )

        return {
            "message": "Clarification processed successfully.",
            "conversation": resolved_conversation
        }

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


@router.post("/preview-sql-prompt")
def preview_sql_prompt(request: RelevanceRequest):
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
            raise ValueError(
                "SQL prompt cannot be built for an irrelevant question."
            )

        ambiguity_result = detect_question_ambiguity(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        if ambiguity_result["is_ambiguous"]:
            raise ValueError(
                "Question requires clarification before SQL prompt generation."
            )

        prompt = build_text_to_sql_prompt(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        return {
            "message": "Text-to-SQL prompt built successfully.",
            "question": processed_question["normalized_question"],
            "prompt": prompt
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


@router.post("/preview-resolved-sql-prompt")
def preview_resolved_sql_prompt(
    request: ResolvedPromptRequest
):
    try:
        conversation_context = get_resolved_conversation_context(
            request.conversation_id
        )

        prompt = build_text_to_sql_prompt(
            question=conversation_context["question"],
            schema_context=conversation_context["schema_context"]
        )

        return {
            "message": "Resolved Text-to-SQL prompt built successfully.",
            "conversation_id": conversation_context["conversation_id"],
            "question": conversation_context["question"],
            "prompt": prompt
        }

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error