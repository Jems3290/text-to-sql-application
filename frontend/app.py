import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 120

st.set_page_config(page_title="Conversational Text-to-SQL", page_icon="💬", layout="wide")


def initialize_state() -> None:
    defaults = {
        "database_id": None,
        "database_name": None,
        "messages": [],
        "pending_conversation_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def api_url(path: str) -> str:
    base_url = st.session_state.get("api_base_url", DEFAULT_API_URL)
    return f"{base_url.rstrip('/')}{path}"


def response_error(response: requests.Response) -> str:
    try:
        payload = response.json()
        return str(payload.get("detail") or payload.get("message") or payload)
    except requests.JSONDecodeError:
        return response.text or f"Request failed with status {response.status_code}."


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(api_url(path), json=payload, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as error:
        raise RuntimeError(
            "Could not connect to the API. Start FastAPI with "
            "`uvicorn backend.main:app --reload`."
        ) from error
    if not response.ok:
        raise RuntimeError(response_error(response))
    return response.json()


def upload_database(uploaded_file: Any) -> None:
    try:
        response = requests.post(
            api_url("/database/upload"),
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/vnd.sqlite3")},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            "Could not connect to the API. Start FastAPI with "
            "`uvicorn backend.main:app --reload`."
        ) from error
    if not response.ok:
        raise RuntimeError(response_error(response))

    database = response.json()["database"]
    st.session_state.database_id = database["database_id"]
    st.session_state.database_name = database["original_filename"]
    st.session_state.messages = []
    st.session_state.pending_conversation_id = None


def result_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    execution = result.get("execution_result") or {}
    rows = execution.get("rows") or []
    columns = execution.get("columns") or []
    if rows and columns and not isinstance(rows[0], dict):
        return [dict(zip(columns, row)) for row in rows]
    return rows


def render_details(payload: dict[str, Any]) -> None:
    result = payload.get("result") or {}
    rows = result_rows(result)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if result.get("effective_sql"):
        with st.expander("Generated SQL"):
            st.code(result["effective_sql"], language="sql")
    with st.expander("Pipeline details"):
        st.json(payload)


def render_assistant_message(message: dict[str, Any]) -> None:
    payload = message.get("payload") or {}
    status = payload.get("status")
    if status == "clarification_required":
        clarification = payload.get("clarification") or {}
        st.markdown(clarification.get("clarification_question") or payload.get("message"))
    elif status == "irrelevant":
        st.warning((payload.get("relevance") or {}).get("reason") or payload.get("message"))
    elif status == "error":
        st.error(payload.get("message", "The request failed."))
    else:
        result = payload.get("result") or {}
        natural_response = result.get("natural_response")
        if isinstance(natural_response, dict):
            text = next(
                (natural_response.get(key) for key in ("answer", "response", "message") if natural_response.get(key)),
                str(natural_response),
            )
        else:
            text = natural_response
        st.markdown(text or payload.get("message", "Query completed."))
        render_details(payload)


def submit_message(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    if st.session_state.pending_conversation_id:
        payload = post_json(
            "/chat/clarify",
            {"conversation_id": st.session_state.pending_conversation_id, "answer": prompt},
        )
        st.session_state.pending_conversation_id = None
    else:
        payload = post_json(
            "/chat/query",
            {"database_id": st.session_state.database_id, "question": prompt},
        )
        if payload.get("status") == "clarification_required":
            st.session_state.pending_conversation_id = payload.get("conversation_id")
    st.session_state.messages.append({"role": "assistant", "content": "", "payload": payload})


initialize_state()
st.title("Conversational Text-to-SQL")
st.caption("Upload a SQLite database and ask questions in plain English.")

with st.sidebar:
    st.header("Database")
    st.session_state.api_base_url = st.text_input(
        "API URL",
        value=os.getenv("TEXT_TO_SQL_API_URL", DEFAULT_API_URL),
        help="Address of the running FastAPI backend.",
    )
    uploaded_file = st.file_uploader("Upload SQLite database", type=["sqlite", "sqlite3", "db"])
    if st.button("Connect database", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.warning("Choose a SQLite database first.")
        else:
            with st.spinner("Uploading and validating database..."):
                try:
                    upload_database(uploaded_file)
                except RuntimeError as error:
                    st.error(str(error))
                else:
                    st.success(f"Connected to {st.session_state.database_name}")
    if st.session_state.database_id:
        st.success(f"Active: {st.session_state.database_name}")
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_conversation_id = None
            st.rerun()

if not st.session_state.database_id:
    st.info("Upload and connect a SQLite database to begin.")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_assistant_message(message)
            else:
                st.markdown(message["content"])

    placeholder = (
        "Answer the clarification question..."
        if st.session_state.pending_conversation_id
        else "Ask a question about your data..."
    )
    if prompt := st.chat_input(placeholder):
        with st.spinner("Analyzing your question..."):
            try:
                submit_message(prompt)
            except RuntimeError as error:
                st.session_state.messages.append(
                    {"role": "assistant", "content": "", "payload": {"status": "error", "message": str(error)}}
                )
        st.rerun()
