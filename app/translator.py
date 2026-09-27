"""
translator.py
--------------
Translates an already-generated list of English QnA pairs into Hindi or
Marathi, preserving the exact question/answer structure so the Excel
sheets line up.
"""

import json
import re
from app.llm_client import get_client, call_with_retry, clean_json_response, LLMError

LANGUAGE_NAMES = {"hi": "Hindi", "mr": "Marathi"}


class TranslationError(Exception):
    pass


def translate_qna_pairs(qna_pairs: list, target_lang_code: str) -> list:
    if target_lang_code not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported language code: {target_lang_code}")
    if not qna_pairs:
        raise TranslationError("No QnA pairs were provided to translate.")

    language_name = LANGUAGE_NAMES[target_lang_code]

    try:
        client = get_client()
    except LLMError as e:
        raise TranslationError(str(e))

    system_prompt = (
        f"You are a professional translator. Translate the given English "
        f"Question-Answer pairs into fluent, natural, grammatically correct "
        f"{language_name}, written in the Devanagari script. Preserve the "
        f"original meaning exactly — do not add or remove information. "
        f"Respond ONLY with valid JSON."
    )
    user_prompt = f"""Translate every question and answer below into {language_name}.
Keep the same number of items, in the same order.

{json.dumps({"qna_pairs": qna_pairs}, ensure_ascii=False, indent=2)}

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
        raise TranslationError(str(e))

    cleaned = clean_json_response(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise TranslationError(
                f"The model did not return valid JSON for the {language_name} translation."
            )
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise TranslationError(f"Could not parse {language_name} JSON output: {e}")

    translated = data.get("qna_pairs", [])
    translated = [
        {"question": p["question"].strip(), "answer": p["answer"].strip()}
        for p in translated
        if isinstance(p, dict) and p.get("question") and p.get("answer")
    ]

    if not translated:
        raise TranslationError(
            f"Translation to {language_name} failed — no valid pairs were returned."
        )

    return translated
