from pydantic import BaseModel
from backend.core.config import settings
from backend.llm.llm_client import mistral_client


class RelevanceResult(BaseModel):
    is_relevant: bool
    reason: str
    matched_tables: list[str]
    matched_columns: list[str]


def build_relevance_prompt(question: str, schema_context: str) -> str:
    return f"""
You are a schema-aware relevance classifier for a Text-to-SQL system.

Your task is to determine whether the user's question can reasonably be
answered using information available in the provided SQLite database schema.

DATABASE SCHEMA:
{schema_context}

USER QUESTION:
{question}

Rules:

1. Mark is_relevant as true when the database contains tables or columns
   that could reasonably answer the question.

2. Semantic meaning matters. The user does not need to use the exact table
   or column names.

3. Do not mark a question irrelevant only because it is ambiguous.
   Ambiguity will be handled by another component.

4. Do not invent tables, columns, or relationships that are not present
   in the provided schema.

5. If the question asks for information clearly outside the available
   database schema, mark is_relevant as false.

6. matched_tables must contain only table names that actually appear
   in the provided schema.

7. matched_columns must use the format "table.column" and must contain
   only columns that actually appear in the provided schema.

8. If the question is irrelevant, matched_tables and matched_columns
   should normally be empty lists.

9. Keep the reason short and factual.
""".strip()


def detect_question_relevance(question: str, schema_context: str) -> dict:
   prompt = build_relevance_prompt(question=question, schema_context=schema_context)

   response = mistral_client.chat.parse(
      model=settings.mistral_model,
      messages=[
         {
            "role": "user",
            "content": prompt
         }
      ],
      response_format=RelevanceResult,
      temperature=0
   )

   relevance_result = response.choices[0].message.parsed

   return relevance_result.model_dump()