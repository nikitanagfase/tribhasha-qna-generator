"""
llm_client.py
-------------
Thin, reusable wrapper around the Groq API used by both qna_generator.py
and translator.py. Keeping retry/error logic in one place avoids duplicated
(and inconsistent) exception handling across the project.
"""

import os
import re
import time
from groq import Groq, APIError, APIConnectionError, RateLimitError

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


class LLMError(Exception):
    """Raised when the Groq API cannot be reached or returns something unusable."""
    pass


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMError(
            "GROQ_API_KEY not found. Add it to your .env file "
            "(GROQ_API_KEY=your_key_here) before running the app."
        )
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        raise LLMError(f"Could not initialise Groq client: {e}")


def call_with_retry(client: Groq, messages: list, retries: int = 3, delay: float = 2.0) -> str:
    """Calls the chat completion endpoint, retrying on transient failures."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise LLMError("Groq returned an empty response.")
            return content
        except RateLimitError as e:
            last_error = e
            time.sleep(delay * attempt)  # back off a bit more each retry
        except (APIError, APIConnectionError) as e:
            last_error = e
            time.sleep(delay)
        except LLMError as e:
            last_error = e
            time.sleep(delay)
        except Exception as e:
            # Non-retryable (bad input, auth failure, etc.) — stop immediately
            last_error = e
            break

    raise LLMError(f"Groq API call failed after {retries} attempt(s): {last_error}")


def clean_json_response(raw: str) -> str:
    """Strips markdown code fences some models wrap JSON in, e.g. ```json ... ```."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    return raw
