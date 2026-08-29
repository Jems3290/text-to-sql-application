import sqlite3
from pathlib import Path


ALLOWED_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}
MAX_DATABASE_SIZE = 200 * 1024 * 1024
SQLITE_HEADER = b"SQLite format 3\x00"


def validate_extension(filename: str) -> None:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Only .db, .sqlite, and .sqlite3 files are allowed."
        )


def validate_file_size(file_path: Path) -> None:
    file_size = file_path.stat().st_size

    if file_size == 0:
        raise ValueError("Uploaded database file is empty.")

    if file_size > MAX_DATABASE_SIZE:
        raise ValueError("Uploaded database exceeds the maximum allowed size of 50 MB.")


def validate_sqlite_header(file_path: Path) -> None:
    with file_path.open("rb") as database_file:
        header = database_file.read(16)

    if header != SQLITE_HEADER:
        raise ValueError("The uploaded file is not a valid SQLite database file.")


def validate_sqlite_database(file_path: Path) -> None:
    database_uri = f"file:{file_path.as_posix()}?mode=ro"

    try:
        with sqlite3.connect(database_uri, uri=True) as connection:
            result = connection.execute("PRAGMA quick_check;").fetchone()

            if result is None or result[0] != "ok":
                raise ValueError("SQLite database integrity check failed.")

    except sqlite3.DatabaseError as error:
        raise ValueError("The uploaded file could not be opened as a valid SQLite database.") from error


def validate_uploaded_database(file_path: Path, original_filename: str) -> None:
    validate_extension(original_filename)
    validate_file_size(file_path)
    validate_sqlite_header(file_path)
    validate_sqlite_database(file_path)