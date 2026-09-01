MAX_ROWS_FOR_LLM = 50

def process_query_result(
    execution_result: dict
) -> dict:
    columns = execution_result["columns"]
    rows = execution_result["rows"]

    row_objects = [
        dict(zip(columns, row))
        for row in rows
    ]

    llm_rows = row_objects[:MAX_ROWS_FOR_LLM]

    llm_rows_truncated = (
        len(row_objects) > MAX_ROWS_FOR_LLM
    )

    return {
        "columns": columns,
        "rows": row_objects,
        "row_count": execution_result["row_count"],
        "result_truncated": execution_result[
            "result_truncated"
        ],
        "max_result_rows": execution_result[
            "max_result_rows"
        ],
        "llm_rows": llm_rows,
        "llm_rows_truncated": llm_rows_truncated
    }


def get_effective_sql(
    original_sql: str,
    correction_result: dict | None
) -> str:
    if (
        correction_result
        and correction_result["correction_succeeded"]
        and correction_result["final_sql"]
    ):
        return correction_result["final_sql"]

    return original_sql