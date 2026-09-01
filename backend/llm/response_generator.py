from pydantic import BaseModel

from backend.core.config import settings
from backend.llm.llm_client import mistral_client
from backend.llm.prompts import (
    build_natural_language_response_prompt,
)


class NaturalLanguageResponse(BaseModel):
    answer: str


def generate_natural_language_response(
    question: str,
    sql_query: str,
    processed_result: dict
) -> dict:
    prompt = build_natural_language_response_prompt(
        question=question,
        sql_query=sql_query,
        processed_result=processed_result
    )

    response = mistral_client.chat.parse(
        model=settings.mistral_model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format=NaturalLanguageResponse,
        temperature=0
    )

    response_result = response.choices[0].message.parsed

    return response_result.model_dump()


