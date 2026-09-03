import os
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

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "development-secret-key"
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

        response_data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "database_id": response_data["database"]["database_id"],
                "filename": response_data["database"]["original_filename"],
                "error": None
            }

        return {
            "success": False,
            "database_id": None,
            "filename": None,
            "error": response_data.get(
                "detail",
                "Database upload failed."
            )
        }

    except requests.RequestException:
        return {
            "success": False,
            "database_id": None,
            "filename": None,
            "error": (
                "Could not connect to the FastAPI backend."
            )
        }

    except ValueError:
        return {
            "success": False,
            "database_id": None,
            "filename": None,
            "error": (
                "The backend returned an invalid response."
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

        response_data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "data": response_data,
                "error": None
            }

        return {
            "success": False,
            "data": None,
            "error": response_data.get(
                "detail",
                "Unable to process the question."
            )
        }

    except requests.RequestException:
        return {
            "success": False,
            "data": None,
            "error": (
                "Could not connect to the FastAPI backend."
            )
        }

    except ValueError:
        return {
            "success": False,
            "data": None,
            "error": (
                "The backend returned an invalid response."
            )
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

        response_data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "data": response_data,
                "error": None
            }

        return {
            "success": False,
            "data": None,
            "error": response_data.get(
                "detail",
                "Unable to process the clarification."
            )
        }

    except requests.RequestException:
        return {
            "success": False,
            "data": None,
            "error": (
                "Could not connect to the FastAPI backend."
            )
        }

    except ValueError:
        return {
            "success": False,
            "data": None,
            "error": (
                "The backend returned an invalid response."
            )
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



@app.route("/", methods=["GET", "POST"])
def home():
    upload_message = None
    upload_error = None

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

                upload_message = (
                    "Database uploaded successfully."
                )

            else:
                upload_error = upload_result["error"]

    return render_template(
        "index.html",
        upload_message=upload_message,
        upload_error=upload_error,
        database_id=session.get("database_id"),
        database_filename=session.get(
            "database_filename"
        )
    )


@app.route("/reset-database", methods=["POST"])
def reset_database():
    session.pop("database_id", None)
    session.pop("database_filename", None)
    session.pop("last_clarification_answer", None)
    session.pop("clarification_error", None)

    return redirect(
        url_for("home")
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
            chat_result = send_question_to_backend(
                database_id=database_id,
                question=question
            )

            if chat_result["success"]:
                response_data = chat_result["data"]
                status = response_data.get("status")

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
                        "The backend returned an "
                        "unknown response status."
                    )

            else:
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
        chat_error=chat_error
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
        session["clarification_error"] = (
            clarification_result["error"]
        )

    return redirect(
        url_for("chat")
    )





if __name__ == "__main__":
    app.run(debug=True, port=5000)