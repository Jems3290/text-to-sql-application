import sqlite3
from pathlib import Path

from backend.database.query_executor import (
    execute_read_only_query,
)
from backend.database.schema_builder import (
    generate_schema_context,
)
from backend.database.sql_security import (
    can_execute_sql,
    enforce_sql_security,
)
from backend.database.sql_validator import (
    validate_generated_sql,
)
from backend.llm.clarification_generator import (
    generate_clarification,
)
from backend.llm.response_generator import (
    generate_natural_language_response,
)
from backend.llm.sql_generator import (
    generate_sql_query,
)
from backend.services.ambiguity_detector import (
    detect_question_ambiguity,
)
from backend.services.conversation_manager import (
    create_clarification_session,
    get_resolved_conversation_context,
    resolve_clarification,
)
from backend.services.question_processor import (
    process_user_question,
)
from backend.services.relevance_detector import (
    detect_question_relevance,
)
from backend.services.result_processor import (
    get_effective_sql,
    process_query_result,
)
from backend.services.sql_correction_service import (
    correct_and_retry_sql,
)




def execute_text_to_sql_pipeline(
    question: str,
    schema_context: str,
    database_path: Path
) -> dict:
    sql_result = generate_sql_query(
        question=question,
        schema_context=schema_context
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
                question=question,
                schema_context=schema_context,
                failed_sql=sql_result["sql_query"],
                database_path=database_path,
                initial_error=str(error)
            )

            if correction_result["correction_succeeded"]:
                execution_result = correction_result[
                    "execution_result"
                ]

    effective_sql = get_effective_sql(
        original_sql=sql_result["sql_query"],
        correction_result=correction_result
    )

    processed_result = None
    natural_response = None

    if execution_result is not None:
        processed_result = process_query_result(
            execution_result
        )

        natural_response = generate_natural_language_response(
            question=question,
            sql_query=effective_sql,
            processed_result=processed_result
        )

    return {
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



def process_chat_query(
    question: str,
    database_path: Path
) -> dict:
    processed_question = process_user_question(
        question
    )

    normalized_question = processed_question[
        "normalized_question"
    ]

    schema_info = generate_schema_context(
        database_path
    )

    schema_context = schema_info[
        "schema_context"
    ]

    relevance_result = detect_question_relevance(
        question=normalized_question,
        schema_context=schema_context
    )

    if not relevance_result["is_relevant"]:
        return {
            "status": "irrelevant",
            "message": (
                "The question cannot be answered using "
                "the uploaded database."
            ),
            "processed_question": processed_question,
            "relevance": relevance_result,
            "ambiguity": None,
            "clarification": None,
            "conversation_id": None,
            "result": None
        }

    ambiguity_result = detect_question_ambiguity(
        question=normalized_question,
        schema_context=schema_context
    )

    if ambiguity_result["is_ambiguous"]:
        clarification_result = generate_clarification(
            question=normalized_question,
            schema_context=schema_context,
            ambiguity_result=ambiguity_result
        )

        conversation_id = create_clarification_session(
            original_question=processed_question[
                "original_question"
            ],
            normalized_question=normalized_question,
            database_path=str(database_path),
            schema_context=schema_context,
            ambiguity_result=ambiguity_result,
            clarification_result=clarification_result
        )

        return {
            "status": "clarification_required",
            "message": (
                "The question requires clarification "
                "before SQL can be generated."
            ),
            "processed_question": processed_question,
            "relevance": relevance_result,
            "ambiguity": ambiguity_result,
            "clarification": clarification_result,
            "conversation_id": conversation_id,
            "result": None
        }

    pipeline_result = execute_text_to_sql_pipeline(
        question=normalized_question,
        schema_context=schema_context,
        database_path=database_path
    )

    return {
        "status": "completed",
        "message": "Question processed successfully.",
        "processed_question": processed_question,
        "relevance": relevance_result,
        "ambiguity": ambiguity_result,
        "clarification": None,
        "conversation_id": None,
        "result": pipeline_result
    }



def process_chat_clarification(
    conversation_id: str,
    clarification_answer: str
) -> dict:
    resolve_clarification(
        conversation_id=conversation_id,
        clarification_answer=clarification_answer
    )

    conversation_context = (
        get_resolved_conversation_context(
            conversation_id
        )
    )

    database_path = Path(
        conversation_context["database_path"]
    )

    if not database_path.exists():
        raise LookupError(
            "Uploaded database file no longer exists."
        )

    pipeline_result = execute_text_to_sql_pipeline(
        question=conversation_context["question"],
        schema_context=conversation_context[
            "schema_context"
        ],
        database_path=database_path
    )

    return {
        "status": "completed",
        "message": (
            "Clarification processed successfully."
        ),
        "conversation_id": conversation_id,
        "question": conversation_context["question"],
        "result": pipeline_result
    }



