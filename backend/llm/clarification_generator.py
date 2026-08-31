import json
from pydantic import BaseModel
from backend.core.config import settings
from backend.llm.llm_client import mistral_client


class ClarificationResult(BaseModel):
    clarification_question: str
    suggested_options: list[str]
    clarification_reason: str


def build_clarification_prompt(
    question: str,
    schema_context: str,
    ambiguity_result: dict
) -> str:
    ambiguity_json = json.dumps(
        ambiguity_result,
        indent=2
    )

    return f"""
You are a clarification-question generator for a schema-aware Text-to-SQL system.

The user's question has already been confirmed as relevant to the database
and has also been identified as ambiguous.

Your task is to generate one concise clarification question that resolves
the detected ambiguity before SQL generation.

DATABASE SCHEMA:
{schema_context}

ORIGINAL USER QUESTION:
{question}

AMBIGUITY ANALYSIS:
{ambiguity_json}

Rules:

1. Generate exactly one primary clarification question.

2. The clarification must directly address the missing information reported
   by the ambiguity analysis.

3. Use only information, concepts, columns, tables, and relationships that
   are supported by the provided database schema.

4. Never invent criteria or fields that do not exist in the schema.

5. suggested_options should contain only options that can reasonably be
   supported using the available schema.

6. Do not invent arbitrary numeric thresholds, dates, names, categories,
   or other values when they are not known from the schema.

7. If useful schema-supported options cannot be determined safely,
   return an empty suggested_options list and ask an open clarification.

8. Do not generate SQL.

9. Do not answer the user's original question.

10. Do not assume what the user intended.

11. Keep the clarification question short, natural, and easy to answer.

12. Keep clarification_reason short and factual.
""".strip()


def generate_clarification(
    question: str,
    schema_context: str,
    ambiguity_result: dict
) -> dict:
    prompt = build_clarification_prompt(
        question=question,
        schema_context=schema_context,
        ambiguity_result=ambiguity_result
    )

    response = mistral_client.chat.parse(
        model=settings.mistral_model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format=ClarificationResult,
        temperature=0
    )

    clarification_result = response.choices[0].message.parsed

    return clarification_result.model_dump()