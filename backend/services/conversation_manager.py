from uuid import uuid4


MAX_CLARIFICATION_LENGTH = 500

conversation_store: dict[str, dict] = {}


def normalize_clarification_answer(answer: str) -> str:
    normalized_answer = " ".join(answer.split())

    return normalized_answer


def validate_clarification_answer(answer: str) -> None:
    if not answer:
        raise ValueError("Clarification answer cannot be empty.")

    if len(answer) > MAX_CLARIFICATION_LENGTH:
        raise ValueError(
            f"Clarification answer cannot exceed {MAX_CLARIFICATION_LENGTH} characters."
        )


def create_clarification_session(
    original_question: str,
    normalized_question: str,
    database_path: str,
    schema_context: str,
    ambiguity_result: dict,
    clarification_result: dict
) -> str:
    conversation_id = str(uuid4())

    conversation_store[conversation_id] = {
        "conversation_id": conversation_id,
        "original_question": original_question,
        "normalized_question": normalized_question,
        "database_path": database_path,
        "schema_context": schema_context,
        "ambiguity_result": ambiguity_result,
        "clarification_result": clarification_result,
        "clarification_answer": None,
        "resolved_question": None,
        "status": "awaiting_clarification"
    }

    return conversation_id


def get_clarification_session(conversation_id: str) -> dict:
    conversation = conversation_store.get(conversation_id)

    if conversation is None:
        raise LookupError("Conversation not found.")

    return conversation


def build_resolved_question(
    normalized_question: str,
    clarification_answer: str
) -> str:
    return (
        f"{normalized_question} "
        f"Clarification answer: {clarification_answer}"
    )


def resolve_clarification(
    conversation_id: str,
    clarification_answer: str
) -> dict:
    conversation = get_clarification_session(conversation_id)

    if conversation["status"] != "awaiting_clarification":
        raise ValueError("This conversation has already been resolved.")

    normalized_answer = normalize_clarification_answer(
        clarification_answer
    )

    validate_clarification_answer(normalized_answer)

    resolved_question = build_resolved_question(
        normalized_question=conversation["normalized_question"],
        clarification_answer=normalized_answer
    )

    conversation["clarification_answer"] = normalized_answer
    conversation["resolved_question"] = resolved_question
    conversation["status"] = "resolved"

    return {
        "conversation_id": conversation_id,
        "original_question": conversation["original_question"],
        "clarification_question": conversation[
            "clarification_result"
        ]["clarification_question"],
        "clarification_answer": normalized_answer,
        "resolved_question": resolved_question,
        "status": conversation["status"]
    }


def get_resolved_conversation_context(
    conversation_id: str
) -> dict:
    conversation = get_clarification_session(conversation_id)

    if conversation["status"] != "resolved":
        raise ValueError(
            "Conversation is still awaiting clarification."
        )

    return {
        "conversation_id": conversation_id,
        "question": conversation["resolved_question"],
        "schema_context": conversation["schema_context"],
        "database_path": conversation["database_path"]
    }