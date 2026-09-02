from pathlib import Path
from uuid import uuid4


database_registry: dict[str, Path] = {}


def register_database(
    database_path: Path
) -> str:
    database_id = str(uuid4())

    database_registry[database_id] = (
        database_path.resolve()
    )

    return database_id


def get_database_path(
    database_id: str
) -> Path:
    database_path = database_registry.get(
        database_id
    )

    if database_path is None:
        raise LookupError(
            "Database session not found."
        )

    if not database_path.exists():
        raise LookupError(
            "Uploaded database file no longer exists."
        )

    return database_path