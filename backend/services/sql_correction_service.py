import sqlite3
from pathlib import Path
from backend.llm.sql_generator import correct_sql_query
from backend.database.sql_validator import validate_generated_sql
from backend.database.query_executor import execute_read_only_query, can_execute_sql
from backend.database.sql_security import enforce_sql_security

MAX_SQL_CORRECTION_ATTEMPTS = 2

def create_correction_attempt(
    attempt_number: int,
    failed_sql: str,
    execution_error: str
) -> dict:
    return {
        "attempt_number": attempt_number,
        "failed_sql": failed_sql,
        "execution_error": execution_error,
        "corrected_sql": None,
        "validation": None,
        "security": None,
        "execution_allowed": False,
        "execution_result": None
    }


def correct_and_retry_sql(
    question: str,
    schema_context: str,
    failed_sql: str,
    database_path: Path,
    initial_error: str
) -> dict:
    correction_history: list[dict] = []

    current_failed_sql = failed_sql
    current_error = initial_error

    for attempt_number in range(
        1,
        MAX_SQL_CORRECTION_ATTEMPTS + 1
    ):
        correction_attempt = create_correction_attempt(
            attempt_number=attempt_number,
            failed_sql=current_failed_sql,
            execution_error=current_error
        )

        corrected_sql_result = correct_sql_query(
            question=question,
            schema_context=schema_context,
            failed_sql=current_failed_sql,
            execution_error=current_error
        )

        corrected_sql = corrected_sql_result["sql_query"]

        correction_attempt["corrected_sql"] = corrected_sql

        validation_result = validate_generated_sql(
            sql_query=corrected_sql,
            database_path=database_path
        )

        correction_attempt["validation"] = validation_result

        if validation_result["is_valid"]:
            security_result = enforce_sql_security(
                corrected_sql
            )
        else:
            security_result = None

        correction_attempt["security"] = security_result

        execution_allowed = can_execute_sql(
            validation_result=validation_result,
            security_result=security_result
        )

        correction_attempt[
            "execution_allowed"
        ] = execution_allowed

        if not execution_allowed:
            correction_history.append(
                correction_attempt
            )

            current_failed_sql = corrected_sql

            validation_errors = validation_result.get(
                "errors",
                []
            )

            security_errors = (
                security_result.get("errors", [])
                if security_result
                else []
            )

            combined_errors = (
                validation_errors
                + security_errors
            )

            current_error = (
                "; ".join(combined_errors)
                or "Corrected SQL failed validation or security checks."
            )

            continue

        try:
            execution_result = execute_read_only_query(
                sql_query=corrected_sql,
                database_path=database_path
            )

            correction_attempt[
                "execution_result"
            ] = execution_result

            correction_history.append(
                correction_attempt
            )

            return {
                "correction_succeeded": True,
                "final_sql": corrected_sql,
                "execution_result": execution_result,
                "correction_history": correction_history
            }

        except sqlite3.DatabaseError as error:
            correction_history.append(
                correction_attempt
            )

            current_failed_sql = corrected_sql
            current_error = str(error)

    return {
        "correction_succeeded": False,
        "final_sql": None,
        "execution_result": None,
        "correction_history": correction_history
    }


