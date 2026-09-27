"""
qna_generator.py
-----------------
Takes raw document text and asks the LLM for a fixed number of
context-grounded English Question-Answer pairs, returned as clean JSON.
"""

import json
import re
from app.llm_client import get_client, call_with_retry, clean_json_response, LLMError

# Keeping the prompt within a safe, fast context window instead of
# chunking — deliberately simple, since assignment inputs are short docs.
MAX_CHARS = 15000


class QnAGenerationError(Exception):
    pass


def generate_qna_pairs(document_text: str, num_pairs: int = 12) -> list:
    if not document_text or not document_text.strip():
        raise QnAGenerationError("Input document text is empty.")

    text_for_prompt = document_text[:MAX_CHARS]

    try:
        client = get_client()
    except LLMError as e:
        raise QnAGenerationError(str(e))

    system_prompt = (
        "You are a careful assistant that creates study-style Question-Answer pairs "
        "strictly grounded in the given document text. Never invent facts that are "
        "not present in the text. Respond ONLY with valid JSON, no extra commentary."
    )
    user_prompt = f"""Read the following document text and generate exactly {num_pairs} clear,
well-structured, grammatically correct Question-Answer pairs in English that are
directly answerable from the text below. Cover the most important points first.

Document text:
\"\"\"
{text_for_prompt}
\"\"\"

Return ONLY valid JSON in this exact structure, nothing else:
{{
  "qna_pairs": [
    {{"question": "...", "answer": "..."}}
  ]
}}
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = call_with_retry(client, messages)
    except LLMError as e:
        raise QnAGenerationError(str(e))

    cleaned = clean_json_response(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise QnAGenerationError("The model did not return valid JSON for the QnA pairs.")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise QnAGenerationError(f"Could not parse the model's JSON output: {e}")

    pairs = data.get("qna_pairs", [])
    pairs = [
        {"question": p["question"].strip(), "answer": p["answer"].strip()}
        for p in pairs
        if isinstance(p, dict) and p.get("question") and p.get("answer")
    ]

    if not pairs:
        raise QnAGenerationError(
            "No valid QnA pairs were generated. Try a longer or clearer document."
        )

    return pairs
