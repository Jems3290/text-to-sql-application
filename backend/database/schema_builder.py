from pathlib import Path
from backend.database.relationship_analyzer import analyze_database_relationships
from backend.database.schema_extractor import extract_database_schema

def build_schema_representation(database_path: Path) -> dict:
    schema = extract_database_schema(database_path)
    relationship_info = analyze_database_relationships(database_path)

    return {
        "table_count": schema["table_count"],
        "tables": schema["tables"],
        "relationship_count": relationship_info["relationship_count"],
        "relationships": relationship_info["relationships"]
    }


def format_column_for_context(column: dict) -> str:
    parts = [
        column["name"],
        column["data_type"] or "UNKNOWN"
    ]

    if column["primary_key_position"] > 0:
        parts.append("PRIMARY KEY")

    if column["not_null"]:
        parts.append("NOT NULL")

    if column["default_value"] is not None:
        parts.append(f"DEFAULT {column['default_value']}")

    return " ".join(parts)


def build_schema_context(schema_representation: dict) -> str:
    context_lines = []

    for table in schema_representation["tables"]:
        context_lines.append(f"Table: {table['table_name']}")
        context_lines.append("Columns:")

        for column in table["columns"]:
            formatted_column = format_column_for_context(column)
            context_lines.append(f"- {formatted_column}")

        context_lines.append("")

    context_lines.append("Relationships:")

    relationships = schema_representation["relationships"]

    if relationships:
        for relationship in relationships:
            context_lines.append(
                "- "
                f"{relationship['source_table']}."
                f"{relationship['source_column']} -> "
                f"{relationship['target_table']}."
                f"{relationship['target_column']}"
            )
    else:
        context_lines.append("- No declared foreign-key relationships.")

    return "\n".join(context_lines).strip()


def generate_schema_context(database_path: Path) -> dict:
    schema_representation = build_schema_representation(database_path)
    schema_context = build_schema_context(schema_representation)

    return {
        "schema_representation": schema_representation,
        "schema_context": schema_context
    }