import re

import sqlglot
from sqlglot import exp


def create_security_result() -> dict:
    return {
        "is_safe": False,
        "is_read_only": False,
        "statement_type": None,
        "blocked_operations": [],
        "errors": []
    }


def parse_security_statement(sql_query: str):
    if not sql_query or not sql_query.strip():
        raise ValueError("SQL query cannot be empty.")

    try:
        statements = sqlglot.parse(
            sql_query,
            read="sqlite"
        )
    except sqlglot.errors.ParseError as error:
        raise ValueError(
            f"Unable to perform SQL security analysis: {error}"
        ) from error

    if len(statements) != 1:
        raise ValueError(
            "Only one SQL statement is allowed."
        )

    return statements[0]


def get_statement_type(parsed_statement) -> str:
    return parsed_statement.key.lower()

BLOCKED_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
    exp.Transaction,
)

def find_blocked_operations(parsed_statement) -> list[str]:
    blocked_operations: list[str] = []

    for expression_type in BLOCKED_EXPRESSION_TYPES:
        for expression in parsed_statement.find_all(expression_type):
            operation_name = expression.key.upper()

            if operation_name not in blocked_operations:
                blocked_operations.append(operation_name)

    return blocked_operations


BLOCKED_SQL_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
    "ANALYZE",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "RELEASE"
}

def find_blocked_keywords(sql_query: str) -> list[str]:
    normalized_sql = sql_query.upper()

    blocked_keywords = [
        keyword
        for keyword in BLOCKED_SQL_KEYWORDS
        if keyword in normalized_sql
    ]

    return sorted(blocked_keywords)


def is_read_only_statement(parsed_statement) -> bool:
    if isinstance(parsed_statement, exp.Select):
        return True

    if isinstance(parsed_statement, exp.Union):
        return True

    return False


def evaluate_read_only_status(
    parsed_statement,
    blocked_operations: list[str]
) -> bool:
    if blocked_operations:
        return False

    return is_read_only_statement(parsed_statement)


def enforce_sql_security(sql_query: str) -> dict:
    security_result = create_security_result()

    try:
        parsed_statement = parse_security_statement(sql_query)
    except ValueError as error:
        security_result["errors"].append(str(error))
        return security_result

    statement_type = get_statement_type(parsed_statement)

    security_result["statement_type"] = statement_type

    blocked_operations = find_blocked_operations(
        parsed_statement
    )

    keyword_matches = find_blocked_keywords(
        sql_query
    )

    for keyword in keyword_matches:
        if keyword not in blocked_operations:
            blocked_operations.append(keyword)

    security_result["blocked_operations"] = sorted(
        blocked_operations
    )

    security_result["is_read_only"] = evaluate_read_only_status(
        parsed_statement=parsed_statement,
        blocked_operations=blocked_operations
    )

    if not security_result["is_read_only"]:
        security_result["errors"].append(
            "SQL query is not a permitted read-only statement."
        )

    if security_result["blocked_operations"]:
        security_result["errors"].append(
            "Blocked SQL operations were detected: "
            + ", ".join(security_result["blocked_operations"])
            + "."
        )

    security_result["is_safe"] = (
        security_result["is_read_only"]
        and len(security_result["blocked_operations"]) == 0
        and len(security_result["errors"]) == 0
    )

    return security_result


def find_blocked_keywords(sql_query: str) -> list[str]:
    normalized_sql = sql_query.upper()

    blocked_keywords: list[str] = []

    for keyword in BLOCKED_SQL_KEYWORDS:
        pattern = rf"\b{re.escape(keyword)}\b"

        if re.search(pattern, normalized_sql):
            blocked_keywords.append(keyword)

    return sorted(blocked_keywords)


