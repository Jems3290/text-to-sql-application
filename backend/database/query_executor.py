import sqlite3
from pathlib import Path

MAX_RESULT_ROWS = 1000

def open_read_only_connection(
    database_path: Path
) -> sqlite3.Connection:
    database_uri = database_path.resolve().as_uri() + "?mode=ro"

    connection = sqlite3.connect(
        database_uri,
        uri=True
    )

    return connection


def convert_rows_to_lists(
    rows: list[tuple]
) -> list[list]:
    return [
        list(row)
        for row in rows
    ]


def execute_read_only_query(
    sql_query: str,
    database_path: Path
) -> dict:
    connection = None

    try:
        connection = open_read_only_connection(
            database_path
        )

        cursor = connection.cursor()

        cursor.execute(sql_query)

        column_names = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchmany(
            MAX_RESULT_ROWS + 1
        )

        result_truncated = (
            len(rows) > MAX_RESULT_ROWS
        )

        if result_truncated:
            rows = rows[:MAX_RESULT_ROWS]

        serialized_rows = convert_rows_to_lists(
            rows
        )

        return {
            "columns": column_names,
            "rows": serialized_rows,
            "row_count": len(serialized_rows),
            "result_truncated": result_truncated,
            "max_result_rows": MAX_RESULT_ROWS
        }

    finally:
        if connection is not None:
            connection.close()


def can_execute_sql(
    validation_result: dict | None,
    security_result: dict | None
) -> bool:
    if not validation_result or not validation_result.get("is_valid", False):
        return False

    if not security_result or not security_result.get("is_safe", False):
        return False

    return True