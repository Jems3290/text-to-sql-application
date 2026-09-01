from pydantic import BaseModel
from backend.core.config import settings
from backend.llm.llm_client import mistral_client
from backend.llm.prompts import build_text_to_sql_prompt


class SQLGenerationResult(BaseModel):
    sql_query: str


def generate_sql_query(
    question: str,
    schema_context: str
) -> dict:
    prompt = build_text_to_sql_prompt(
        question=question,
        schema_context=schema_context
    )

    response = mistral_client.chat.parse(
        model=settings.mistral_model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format=SQLGenerationResult,
        temperature=0
    )

    sql_result = response.choices[0].message.parsed

    normalized_sql = normalize_generated_sql(
        sql_result.sql_query
    )

    return {
        "sql_query": normalized_sql
    }


def normalize_generated_sql(sql_query: str) -> str:
    normalized_sql = sql_query.strip()

    if not normalized_sql.endswith(";"):
        normalized_sql += ";"

    return normalized_sql