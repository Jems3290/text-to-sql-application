from pydantic import BaseModel
from backend.core.config import settings
from backend.llm.llm_client import mistral_client


class AmbiguityResult(BaseModel):
    is_ambiguous: bool
    reason: str
    ambiguity_types: list[str]
    ambiguous_terms: list[str]
    missing_information: list[str]


def build_ambiguity_prompt(
    question: str,
    schema_context: str
) -> str:
    return f"""
You are an ambiguity detector for a schema-aware Text-to-SQL system.

The user's question has already been classified as relevant to the database.

Your task is to determine whether the question contains enough information
to generate one clear and well-defined SQL query.

DATABASE SCHEMA:
{schema_context}

USER QUESTION:
{question}

Rules:

1. Mark is_ambiguous as true only when important information is missing
   and multiple materially different SQL interpretations are reasonable.

2. Do not mark a question ambiguous just because it uses natural language
   instead of exact table or column names.

3. Do not treat missing database information as ambiguity. If the requested
   information does not exist in the schema, that belongs to relevance
   detection rather than ambiguity detection.

4. Consider undefined ranking criteria ambiguous.
   Example: "Show the best employee" when "best" has no stated criterion.

5. Consider undefined qualitative thresholds ambiguous.
   Examples include "high salary", "low score", or "large order" when no
   threshold or rule is specified.

6. Consider vague time expressions ambiguous when they cannot be converted
   into one clear time condition from the question.
   Examples include "recent", "old", or "for some time".

7. Consider missing filter values ambiguous when the question requires a
   specific value but does not provide one.
   Example: "Show students from a department" without identifying which
   department.

8. Do not mark clearly defined requests ambiguous.
   Examples:
   "Show all students."
   "Show employees with salary greater than 50000."
   "Show students enrolled after 2023."

9. ambiguity_types should contain short categories such as:
   "ranking_criterion", "threshold", "time_range", "filter_value",
   "aggregation", "comparison", "limit", or "other".

10. ambiguous_terms should contain only the words or phrases from the
    user's question that cause ambiguity.

11. missing_information should clearly describe what must be known before
    one well-defined SQL query can be generated.

12. If is_ambiguous is false, ambiguity_types, ambiguous_terms, and
    missing_information must all be empty lists.

13. Keep the reason short and factual.

Do not generate SQL.
Do not generate a clarification question.
Only analyze ambiguity.
""".strip()


def detect_question_ambiguity(
    question: str,
    schema_context: str
) -> dict:
    prompt = build_ambiguity_prompt(
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
        response_format=AmbiguityResult,
        temperature=0
    )

    ambiguity_result = response.choices[0].message.parsed

    return ambiguity_result.model_dump()