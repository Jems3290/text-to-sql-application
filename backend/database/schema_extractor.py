import sqlite3
from pathlib import Path

def create_read_only_connection(database_path: Path) -> sqlite3.Connection:
    database_uri = f"file:{database_path.as_posix()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)

    return connection


def extract_table_names(connection: sqlite3.Connection) -> list[str]:
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """

    rows = connection.execute(query).fetchall()

    return [row[0] for row in rows]


def extract_table_columns(
    connection: sqlite3.Connection,
    table_name: str
) -> list[dict]:
    rows = connection.execute(
        f'PRAGMA table_info("{table_name}");'
    ).fetchall()

    columns = []

    for row in rows:
        column = {
            "column_id": row[0],
            "name": row[1],
            "data_type": row[2],
            "not_null": bool(row[3]),
            "default_value": row[4],
            "primary_key_position": row[5]
        }

        columns.append(column)

    return columns


def extract_database_schema(database_path: Path) -> dict:
    connection = create_read_only_connection(database_path)

    try:
        table_names = extract_table_names(connection)

        schema = {
            "database_path": str(database_path),
            "table_count": len(table_names),
            "tables": []
        }

        for table_name in table_names:
            columns = extract_table_columns(
                connection=connection,
                table_name=table_name
            )

            schema["tables"].append(
                {
                    "table_name": table_name,
                    "column_count": len(columns),
                    "columns": columns
                }
            )

        return schema

    finally:
        connection.close()