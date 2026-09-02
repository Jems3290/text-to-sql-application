from mistralai.client.models import cancel_workflow_execution_v1_workflows_executions_execution_id_cancel_postop
from mistralai.client.models import cancel_workflow_execution_v1_workflows_executions_execution_id_cancel_postop
import sqlite3
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.llm.prompts import build_text_to_sql_prompt
from backend.llm.sql_generator import generate_sql_query
from backend.database.sql_security import enforce_sql_security
from backend.services.database_registry import get_database_path
from backend.database.sql_validator import validate_generated_sql
from backend.database.schema_builder import generate_schema_context
from backend.services.question_processor import process_user_question
from backend.llm.clarification_generator import generate_clarification
from backend.services.ambiguity_detector import detect_question_ambiguity
from backend.services.relevance_detector import detect_question_relevance
from backend.services.sql_correction_service import correct_and_retry_sql
from backend.llm.response_generator import generate_natural_language_response
from backend.database.query_executor import can_execute_sql, execute_read_only_query
from backend.services.result_processor import get_effective_sql, process_query_result
from backend.services.chat_service import process_chat_clarification, process_chat_query
from backend.services.conversation_manager import create_clarification_session, get_resolved_conversation_context, resolve_clarification


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

class ChatQueryRequest(BaseModel):
    database_id: str
    question: str

class ChatClarificationRequest(BaseModel):
    conversation_id: str
    answer: str

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


@router.post("/generate-sql")
def generate_sql(request: RelevanceRequest):
    database_path = Path(request.database_path)

    if not database_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Database file not found."
        )

    try:
        processed_question = process_user_question(
            request.question
        )

        schema_context_info = generate_schema_context(
            database_path
        )

        relevance_result = detect_question_relevance(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        if not relevance_result["is_relevant"]:
            raise ValueError(
                "SQL cannot be generated for an irrelevant question."
            )

        ambiguity_result = detect_question_ambiguity(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        if ambiguity_result["is_ambiguous"]:
            raise ValueError(
                "Question requires clarification before SQL generation."
            )

        sql_result = generate_sql_query(
            question=processed_question["normalized_question"],
            schema_context=schema_context_info["schema_context"]
        )

        validation_result = validate_generated_sql(
            sql_query=sql_result["sql_query"],
            database_path=database_path
        )

        if validation_result["is_valid"]:
            security_result = enforce_sql_security(
                sql_result["sql_query"]
            )
        else:
            security_result = None

        execution_allowed = can_execute_sql(
            validation_result=validation_result,
            security_result=security_result
        )

        execution_result = None
        correction_result = None

        if execution_allowed:
            try:
                execution_result = execute_read_only_query(
                    sql_query=sql_result["sql_query"],
                    database_path=database_path
                )

            except sqlite3.DatabaseError as error:
                correction_result = correct_and_retry_sql(
                    question=processed_question["normalized_question"],
                    schema_context=schema_context_info["schema_context"],
                    failed_sql=sql_result["sql_query"],
                    database_path=database_path,
                    initial_error=str(error)
                )

                if correction_result["correction_succeeded"]:
                    execution_result = correction_result[
                        "execution_result"
                    ]

        processed_result = None
        natural_response = None

        effective_sql = get_effective_sql(
            original_sql=sql_result["sql_query"],
            correction_result=correction_result
        )

        if execution_result is not None:
            processed_result = process_query_result(
                execution_result
            )

            natural_response = generate_natural_language_response(
                question=processed_question["normalized_question"],
                sql_query=effective_sql,
                processed_result=processed_result
            )

        return {
            "message": "Question processed successfully through the complete Text-to-SQL pipeline.",
            "processed_question": processed_question,
            "relevance": relevance_result,
            "ambiguity": ambiguity_result,
            "sql_generation": sql_result,
            "sql_validation": validation_result,
            "sql_security": security_result,
            "execution_allowed": execution_allowed,
            "effective_sql": effective_sql,
            "execution_result": execution_result,
            "correction": correction_result,
            "processed_result": processed_result,
            "natural_response": natural_response
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


@router.post("/generate-resolved-sql")
def generate_resolved_sql(
    request: ResolvedPromptRequest
):
    try:
        conversation_context = get_resolved_conversation_context(
            request.conversation_id
        )

        database_path = Path(
            conversation_context["database_path"]
        )

        if not database_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Database file not found."
            )

        sql_result = generate_sql_query(
            question=conversation_context["question"],
            schema_context=conversation_context["schema_context"]
        )

        validation_result = validate_generated_sql(
            sql_query=sql_result["sql_query"],
            database_path=database_path
        )

        if validation_result["is_valid"]:
            security_result = enforce_sql_security(
                sql_result["sql_query"]
            )
        else:
            security_result = None

        execution_allowed = can_execute_sql(
            validation_result=validation_result,
            security_result=security_result
        )

        execution_result = None
        correction_result = None

        if execution_allowed:
            try:
                execution_result = execute_read_only_query(
                    sql_query=sql_result["sql_query"],
                    database_path=database_path
                )

            except sqlite3.DatabaseError as error:
                correction_result = correct_and_retry_sql(
                    question=conversation_context["question"],
                    schema_context=conversation_context["schema_context"],
                    failed_sql=sql_result["sql_query"],
                    database_path=database_path,
                    initial_error=str(error)
                )

                if correction_result["correction_succeeded"]:
                    execution_result = correction_result[
                        "execution_result"
                    ]

        processed_result = None
        natural_response = None

        effective_sql = get_effective_sql(
            original_sql=sql_result["sql_query"],
            correction_result=correction_result
        )

        if execution_result is not None:
            processed_result = process_query_result(
                execution_result
            )

            natural_response = generate_natural_language_response(
                question=conversation_context["question"],
                sql_query=effective_sql,
                processed_result=processed_result
            )

        return {
            "message": "Resolved conversation processed successfully through the complete Text-to-SQL pipeline.",
            "conversation_id": conversation_context["conversation_id"],
            "question": conversation_context["question"],
            "sql_generation": sql_result,
            "sql_validation": validation_result,
            "sql_security": security_result,
            "execution_allowed": execution_allowed,
            "effective_sql": effective_sql,
            "execution_result": execution_result,
            "correction": correction_result,
            "processed_result": processed_result,
            "natural_response": natural_response
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

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


@router.post("/query")
def chat_query(
    request: ChatQueryRequest
):
    try:
        database_path = get_database_path(
            request.database_id
        )

        return process_chat_query(
            question=request.question,
            database_path=database_path
        )

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

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


@router.post("/clarify")
def chat_clarify(
    request: ChatClarificationRequest
):
    try:
        return process_chat_clarification(
            conversation_id=request.conversation_id,
            clarification_answer=request.answer
        )

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

    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


