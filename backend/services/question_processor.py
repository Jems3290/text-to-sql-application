MAX_QUESTION_LENGTH = 1000

def normalize_question(question: str) -> str:
    normalized_question = " ".join(question.split())

    return normalized_question


def validate_question(question: str) -> None:
    if not question:
        raise ValueError("Question cannot be empty.")

    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(
            f"Question cannot exceed {MAX_QUESTION_LENGTH} characters."
        )


def process_user_question(question: str) -> dict:
    original_question = question
    normalized_question = normalize_question(question)

    validate_question(normalized_question)

    return {
        "original_question": original_question,
        "normalized_question": normalized_question,
        "character_count": len(normalized_question),
        "word_count": len(normalized_question.split())
    }