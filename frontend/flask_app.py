import os
from uuid import uuid4

import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for
)

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ[
    "FLASK_SECRET_KEY"
]

chat_result_store = {}


def get_chat_state_id() -> str:
    chat_state_id = session.get(
        "chat_state_id"
    )

    if not chat_state_id:
        chat_state_id = str(uuid4())

        session["chat_state_id"] = (
            chat_state_id
        )

    return chat_state_id

def save_query_details(
    query_details: dict
) -> None:
    chat_state_id = get_chat_state_id()

    chat_result_store[
        chat_state_id
    ] = query_details

def get_query_details():
    chat_state_id = session.get(
        "chat_state_id"
    )

    if not chat_state_id:
        return None

    return chat_result_store.get(
        chat_state_id
    )

def clear_query_details() -> None:
    chat_state_id = session.get(
        "chat_state_id"
    )

    if chat_state_id:
        chat_result_store.pop(
            chat_state_id,
            None
        )

def upload_database_to_backend(
    database_file
) -> dict:
    try:
        files = {
            "file": (
                database_file.filename,
                database_file.stream,
                database_file.mimetype
            )
        }

        response = requests.post(
            f"{FASTAPI_BASE_URL}/database/upload",
            files=files,
            timeout=30
        )

        try:
            response_data = response.json()
        except ValueError:
            return {
                "success": False,
                "database_id": None,
                "filename": None,
                "error": (
                    "The backend returned an invalid response."
                )
            }

        if response.status_code == 200:
            database_data = (
                response_data.get("database")
                or {}
            )

            database_id = database_data.get(
                "database_id"
            )

            filename = database_data.get(
                "original_filename"
            )

            if not database_id:
                return {
                    "success": False,
                    "database_id": None,
                    "filename": None,
                    "error": (
                        "The backend response did not contain "
                        "a database ID."
                    )
                }

            return {
                "success": True,
                "database_id": database_id,
                "filename": (
                    filename
                    or database_file.filename
                ),
                "error": None
            }

        error_message = response_data.get(
            "detail"
        )

        if not error_message:
            error_message = (
                "Database upload failed."
            )

        return {
            "success": False,
            "database_id": None,
            "filename": None,
            "error": error_message
        }

    except requests.Timeout:
        return {
            "success": False,
            "database_id": None,
            "filename": None,
            "error": (
                "Database upload timed out. "
                "Please try again."
            )
        }

    except requests.ConnectionError:
        return {
            "success": False,
            "database_id": None,
            "filename": None,
            "error": (
                "Could not connect to the FastAPI backend."
            )
        }

    except requests.RequestException:
        return {
            "success": False,
            "database_id": None,
            "filename": None,
            "error": (
                "A network error occurred while uploading "
                "the database."
            )
        }

def send_question_to_backend(
    database_id: str,
    question: str
) -> dict:
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/chat/query",
            json={
                "database_id": database_id,
                "question": question
            },
            timeout=120
        )

        try:
            response_data = response.json()
        except ValueError:
            return {
                "success": False,
                "data": None,
                "error": (
                    "The backend returned an invalid response."
                ),
                "error_type": "invalid_response"
            }

        if response.status_code == 200:
            return {
                "success": True,
                "data": response_data,
                "error": None,
                "error_type": None
            }

        error_message = response_data.get(
            "detail"
        )

        if not error_message:
            error_message = (
                "Unable to process the question."
            )

        if response.status_code == 404:
            return {
                "success": False,
                "data": None,
                "error": error_message,
                "error_type": "database_not_found"
            }

        return {
            "success": False,
            "data": None,
            "error": error_message,
            "error_type": "backend_error"
        }

    except requests.Timeout:
        return {
            "success": False,
            "data": None,
            "error": (
                "The question took too long to process. "
                "Please try again."
            ),
            "error_type": "timeout"
        }

    except requests.ConnectionError:
        return {
            "success": False,
            "data": None,
            "error": (
                "Could not connect to the FastAPI backend."
            ),
            "error_type": "connection"
        }

    except requests.RequestException:
        return {
            "success": False,
            "data": None,
            "error": (
                "A network error occurred while processing "
                "the question."
            ),
            "error_type": "network"
        }

def send_clarification_to_backend(
    conversation_id: str,
    answer: str
) -> dict:
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/chat/clarify",
            json={
                "conversation_id": conversation_id,
                "answer": answer
            },
            timeout=120
        )

        try:
            response_data = response.json()
        except ValueError:
            return {
                "success": False,
                "data": None,
                "error": (
                    "The backend returned an invalid response."
                ),
                "error_type": "invalid_response"
            }

        if response.status_code == 200:
            return {
                "success": True,
                "data": response_data,
                "error": None,
                "error_type": None
            }

        error_message = response_data.get(
            "detail"
        )

        if not error_message:
            error_message = (
                "Unable to process the clarification."
            )

        if response.status_code == 404:
            return {
                "success": False,
                "data": None,
                "error": error_message,
                "error_type": "conversation_not_found"
            }

        return {
            "success": False,
            "data": None,
            "error": error_message,
            "error_type": "backend_error"
        }

    except requests.Timeout:
        return {
            "success": False,
            "data": None,
            "error": (
                "The clarification took too long to process. "
                "Please try again."
            ),
            "error_type": "timeout"
        }

    except requests.ConnectionError:
        return {
            "success": False,
            "data": None,
            "error": (
                "Could not connect to the FastAPI backend."
            ),
            "error_type": "connection"
        }

    except requests.RequestException:
        return {
            "success": False,
            "data": None,
            "error": (
                "A network error occurred while processing "
                "the clarification."
            ),
            "error_type": "network"
        }

def extract_completed_answer(
    response_data: dict
) -> str:
    result = response_data.get("result") or {}

    natural_response = (
        result.get("natural_response") or {}
    )

    answer = natural_response.get("answer")

    if answer:
        return answer

    return (
        "The query was processed, but no natural-language "
        "response was returned."
    )

def extract_query_details(
    response_data: dict
) -> dict:
    result = response_data.get(
        "result"
    ) or {}

    sql = (
        result.get("effective_sql")
        or result.get("sql_query")
        or result.get("generated_sql")
        or result.get("sql")
    )

    execution_result = (
        result.get("execution_result")
        or result.get("query_result")
        or result.get("execution")
        or {}
    )

    columns = execution_result.get(
        "columns"
    ) or []

    rows = execution_result.get(
        "rows"
    ) or []

    row_count = execution_result.get(
        "row_count"
    )

    truncated = execution_result.get(
        "truncated",
        False
    )

    display_rows = []

    if rows and isinstance(
        rows[0],
        dict
    ):
        if not columns:
            columns = list(
                rows[0].keys()
            )

        for row in rows:
            display_rows.append(
                [
                    row.get(column)
                    for column in columns
                ]
            )

    else:
        display_rows = rows

    if row_count is None:
        row_count = len(display_rows)

    return {
        "sql": sql,
        "columns": columns,
        "rows": display_rows,
        "row_count": row_count,
        "truncated": truncated
    }

def extract_clarification_question(
    response_data: dict
) -> str:
    clarification = (
        response_data.get("clarification") or {}
    )

    clarification_question = (
        clarification.get("clarification_question")
        or clarification.get("question")
    )

    if clarification_question:
        return clarification_question

    return (
        "Your question needs more information. "
        "Please provide additional clarification."
    )

def clear_conversation_state() -> None:
    session.pop("last_question", None)
    session.pop("last_answer", None)
    session.pop(
        "last_clarification_answer",
        None
    )
    session.pop(
        "pending_conversation_id",
        None
    )
    session.pop(
        "clarification_question",
        None
    )
    session.pop(
        "clarification_error",
        None
    )

    clear_query_details()



@app.route("/", methods=["GET", "POST"])
def home():
    upload_message = None
    upload_error = None
    database_error = session.pop(
        "database_error",
        None
    )
    if request.method == "POST":
        database_file = request.files.get("database_file")

        if not database_file or database_file.filename == "":
            upload_error = "Please select a database file."

        else:
            upload_result = upload_database_to_backend(
                database_file
            )

            if upload_result["success"]:
                session["database_id"] = upload_result[
                    "database_id"
                ]
                session["database_filename"] = upload_result[
                    "filename"
                ]
                clear_query_details()
                upload_message = (
                    "Database uploaded successfully."
                )

            else:
                upload_error = upload_result["error"]

    return render_template(
        "index.html",
        database_error=database_error,
        upload_message=upload_message,
        upload_error=upload_error,
        database_id=session.get("database_id"),
        database_filename=session.get(
            "database_filename"
        )
    )



@app.route("/chat", methods=["GET", "POST"])
def chat():
    database_id = session.get("database_id")

    if not database_id:
        return redirect(
            url_for("home")
        )

    chat_error = None

    if request.method == "POST":
        question = request.form.get(
            "question",
            ""
        ).strip()

        if not question:
            chat_error = "Please enter a question."

        else:
            clear_query_details()
            chat_result = send_question_to_backend(
                database_id=database_id,
                question=question
            )

            if chat_result["success"]:
                response_data = chat_result["data"]
                status = response_data.get("status")

                if not status:
                    chat_error = (
                        "The backend response did not contain "
                        "a valid processing status."
                    )

                    return render_template(
                        "chat.html",
                        database_filename=session.get(
                            "database_filename"
                        ),
                        last_question=session.get(
                            "last_question"
                        ),
                        last_answer=session.get(
                            "last_answer"
                        ),
                        last_clarification_answer=session.get(
                            "last_clarification_answer"
                        ),
                        clarification_question=session.get(
                            "clarification_question"
                        ),
                        pending_conversation_id=session.get(
                            "pending_conversation_id"
                        ),
                        clarification_error=session.get(
                            "clarification_error"
                        ),
                        chat_error=chat_error,
                        query_details=get_query_details()
                    )

                session["last_question"] = question

                session.pop(
                    "last_clarification_answer",
                    None
                )

                session.pop(
                    "clarification_error",
                    None
                )

                if status == "completed":
                    answer = extract_completed_answer(
                        response_data
                    )

                    session["last_answer"] = answer
                    query_details = extract_query_details(
                        response_data
                    )

                    save_query_details(
                        query_details
                    )
                    session.pop(
                        "pending_conversation_id",
                        None
                    )
                    session.pop(
                        "clarification_question",
                        None
                    )

                elif status == "clarification_required":
                    conversation_id = response_data.get(
                        "conversation_id"
                    )

                    clarification_question = (
                        extract_clarification_question(
                            response_data
                        )
                    )

                    session[
                        "pending_conversation_id"
                    ] = conversation_id

                    session[
                        "clarification_question"
                    ] = clarification_question

                    session["last_answer"] = (
                        clarification_question
                    )

                elif status == "irrelevant":
                    session["last_answer"] = (
                        response_data.get(
                            "message",
                            (
                                "This question cannot be "
                                "answered using the "
                                "uploaded database."
                            )
                        )
                    )

                else:
                    chat_error = (
                        "The backend returned an unsupported "
                        f"response status: {status}"
                    )

            else:
                error_type = chat_result.get(
                    "error_type"
                )

                if error_type == "database_not_found":
                    session.pop("database_id", None)
                    session.pop(
                        "database_filename",
                        None
                    )

                    clear_conversation_state()

                    session["database_error"] = (
                        "The selected database is no longer "
                        "available. Please upload it again."
                    )

                    return redirect(
                        url_for("home")
                    )

                chat_error = chat_result["error"]

            return render_template(
                "chat.html",
                database_filename=session.get(
                    "database_filename"
                ),
                last_question=session.get(
                    "last_question"
                ),
                last_answer=session.get(
                    "last_answer"
                ),
                last_clarification_answer=session.get(
                    "last_clarification_answer"
                ),
                clarification_question=session.get(
                    "clarification_question"
                ),
                pending_conversation_id=session.get(
                    "pending_conversation_id"
                ),
                clarification_error=session.get(
                    "clarification_error"
                ),
                chat_error=chat_error,
                query_details=get_query_details()
            )

    return render_template(
        "chat.html",
        database_filename=session.get(
            "database_filename"
        ),
        last_question=session.get(
            "last_question"
        ),
        last_answer=session.get(
            "last_answer"
        ),
        last_clarification_answer=session.get(
            "last_clarification_answer"
        ),
        clarification_question=session.get(
            "clarification_question"
        ),
        pending_conversation_id=session.get(
            "pending_conversation_id"
        ),
        clarification_error=session.get(
            "clarification_error"
        ),
        chat_error=chat_error,
        query_details=get_query_details()
    )


@app.route("/reset-database", methods=["POST"])
def reset_database():
    session.pop("database_id", None)
    session.pop("database_filename", None)
    session.pop("last_question", None)
    session.pop("last_answer", None)
    session.pop("pending_conversation_id", None)
    session.pop("clarification_question", None)
    session.pop("last_clarification_answer", None)
    session.pop("clarification_error", None)
    clear_query_details()
    return redirect(url_for("home"))


@app.route("/chat/clarify", methods=["POST"])
def submit_clarification():
    conversation_id = session.get(
        "pending_conversation_id"
    )

    if not conversation_id:
        return redirect(
            url_for("chat")
        )

    clarification_answer = request.form.get(
        "clarification_answer",
        ""
    ).strip()

    if not clarification_answer:
        session["clarification_error"] = (
            "Please enter a clarification answer."
        )

        return redirect(
            url_for("chat")
        )

    clarification_result = (
        send_clarification_to_backend(
            conversation_id=conversation_id,
            answer=clarification_answer
        )
    )

    if clarification_result["success"]:
        response_data = clarification_result["data"]

        answer = extract_completed_answer(
            response_data
        )

        session["last_answer"] = answer
        query_details = extract_query_details(
            response_data
        )

        save_query_details(
            query_details
        )
        session["last_clarification_answer"] = (
            clarification_answer
        )

        session.pop(
            "pending_conversation_id",
            None
        )
        session.pop(
            "clarification_question",
            None
        )
        session.pop(
            "clarification_error",
            None
        )

    else:
        error_type = clarification_result.get(
            "error_type"
        )

        if error_type == "conversation_not_found":
            session.pop(
                "pending_conversation_id",
                None
            )
            session.pop(
                "clarification_question",
                None
            )
            session.pop(
                "last_clarification_answer",
                None
            )

            session["clarification_error"] = (
                "The clarification conversation has "
                "expired. Please ask the original "
                "question again."
            )

        else:
            session["clarification_error"] = (
                clarification_result["error"]
            )

    return redirect(
        url_for("chat")
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)