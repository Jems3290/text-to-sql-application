import sqlite3
from pathlib import Path
from backend.database.schema_extractor import (
    create_read_only_connection,
    extract_table_names,
)


def extract_table_foreign_keys(
    connection: sqlite3.Connection,
    table_name: str
) -> list[dict]:
    rows = connection.execute(
        f'PRAGMA foreign_key_list("{table_name}");'
    ).fetchall()

    foreign_keys = []

    for row in rows:
        foreign_key = {
            "foreign_key_id": row[0],
            "sequence": row[1],
            "referenced_table": row[2],
            "from_column": row[3],
            "to_column": row[4],
            "on_update": row[5],
            "on_delete": row[6],
            "match": row[7]
        }

        foreign_keys.append(foreign_key)

    return foreign_keys


def analyze_database_relationships(
    database_path: Path
) -> dict:
    connection = create_read_only_connection(database_path)

    try:
        table_names = extract_table_names(connection)
        relationships = []

        for table_name in table_names:
            foreign_keys = extract_table_foreign_keys(
                connection=connection,
                table_name=table_name
            )

            for foreign_key in foreign_keys:
                relationship = {
                    "source_table": table_name,
                    "source_column": foreign_key["from_column"],
                    "target_table": foreign_key["referenced_table"],
                    "target_column": foreign_key["to_column"],
                    "foreign_key_id": foreign_key["foreign_key_id"],
                    "sequence": foreign_key["sequence"],
                    "on_update": foreign_key["on_update"],
                    "on_delete": foreign_key["on_delete"]
                }

                relationships.append(relationship)

        return {
            "relationship_count": len(relationships),
            "relationships": relationships
        }

    finally:
        connection.close()