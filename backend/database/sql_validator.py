from pathlib import Path

import sqlglot
from sqlglot import exp

from backend.database.schema_extractor import extract_database_schema


def create_validation_result() -> dict:
    return {
        "is_valid": False,
        "syntax_valid": False,
        "schema_valid": False,
        "referenced_tables": [],
        "referenced_columns": [],
        "errors": []
    }


def parse_sql_query(sql_query: str):
    if not sql_query or not sql_query.strip():
        raise ValueError("Generated SQL query cannot be empty.")

    try:
        parsed_statements = sqlglot.parse(
            sql_query,
            read="sqlite"
        )
    except sqlglot.errors.ParseError as error:
        raise ValueError(
            f"SQL syntax error: {error}"
        ) from error

    if len(parsed_statements) != 1:
        raise ValueError(
            "Generated SQL must contain exactly one SQL statement."
        )

    return parsed_statements[0]


def build_schema_lookup(database_path: Path) -> dict[str, set[str]]:
    database_schema = extract_database_schema(database_path)

    schema_lookup: dict[str, set[str]] = {}

    for table_info in database_schema.get("tables", []):
        table_name = table_info["table_name"]
        column_names = {
            column["name"]
            for column in table_info["columns"]
        }

        schema_lookup[table_name.lower()] = {
            column_name.lower()
            for column_name in column_names
        }

    return schema_lookup


def extract_referenced_tables(parsed_query) -> dict[str, str]:
    referenced_tables: dict[str, str] = {}

    for table in parsed_query.find_all(exp.Table):
        table_name = table.name

        if not table_name:
            continue

        alias_name = table.alias_or_name

        referenced_tables[alias_name.lower()] = table_name.lower()

    return referenced_tables


def validate_referenced_tables(
    referenced_tables: dict[str, str],
    schema_lookup: dict[str, set[str]]
) -> list[str]:
    errors: list[str] = []

    for table_name in referenced_tables.values():
        if table_name not in schema_lookup:
            errors.append(
                f"Table '{table_name}' does not exist in the database schema."
            )

    return errors


def validate_referenced_columns(
    parsed_query,
    referenced_tables: dict[str, str],
    schema_lookup: dict[str, set[str]]
) -> tuple[list[str], list[str]]:
    referenced_columns: list[str] = []
    errors: list[str] = []

    valid_tables = {
        alias: table_name
        for alias, table_name in referenced_tables.items()
        if table_name in schema_lookup
    }

    for column in parsed_query.find_all(exp.Column):
        column_name = column.name.lower()
        table_reference = column.table.lower() if column.table else None

        if table_reference:
            real_table_name = valid_tables.get(table_reference)

            if real_table_name is None:
                errors.append(
                    f"Unknown table or alias '{table_reference}' "
                    f"used for column '{column_name}'."
                )
                continue

            referenced_columns.append(
                f"{real_table_name}.{column_name}"
            )

            if column_name not in schema_lookup[real_table_name]:
                errors.append(
                    f"Column '{column_name}' does not exist "
                    f"in table '{real_table_name}'."
                )

            continue

        matching_tables = [
            table_name
            for table_name in valid_tables.values()
            if column_name in schema_lookup[table_name]
        ]

        unique_matching_tables = sorted(set(matching_tables))

        if not unique_matching_tables:
            errors.append(
                f"Column '{column_name}' does not exist in any "
                f"referenced table."
            )
            continue

        if len(unique_matching_tables) > 1:
            errors.append(
                f"Column '{column_name}' is ambiguous because it exists "
                f"in multiple referenced tables."
            )
            continue

        referenced_columns.append(
            f"{unique_matching_tables[0]}.{column_name}"
        )

    return referenced_columns, errors


def validate_generated_sql(
    sql_query: str,
    database_path: Path
) -> dict:
    validation_result = create_validation_result()

    try:
        parsed_query = parse_sql_query(sql_query)
        validation_result["syntax_valid"] = True
    except ValueError as error:
        validation_result["errors"].append(str(error))
        return validation_result

    schema_lookup = build_schema_lookup(database_path)

    referenced_tables = extract_referenced_tables(parsed_query)

    validation_result["referenced_tables"] = sorted(
        set(referenced_tables.values())
    )

    table_errors = validate_referenced_tables(
        referenced_tables=referenced_tables,
        schema_lookup=schema_lookup
    )

    referenced_columns, column_errors = validate_referenced_columns(
        parsed_query=parsed_query,
        referenced_tables=referenced_tables,
        schema_lookup=schema_lookup
    )

    validation_result["referenced_columns"] = sorted(
        set(referenced_columns)
    )

    validation_result["errors"].extend(table_errors)
    validation_result["errors"].extend(column_errors)

    validation_result["schema_valid"] = (
        len(table_errors) == 0
        and len(column_errors) == 0
    )

    validation_result["is_valid"] = (
        validation_result["syntax_valid"]
        and validation_result["schema_valid"]
    )

    return validation_result


