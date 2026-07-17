from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
import os, time, random
from app.schemas.extraction import MeetingSummary

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

"""
Transient errors worth retrying: 503 (overloaded), 429 (rate limit), 500 (internal).
Anything else should fall immediately - retrying won't help and just hides a real bug.
"""
RETRYABLE_STATUS_CODES = {429, 500, 503}

def _call_gemini_with_retry(prompt: str, max_retries: int = 4, base_delay: float = 2.0):
    last_exception = None
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MeetingSummary,
                ),
            )
        except errors.APIError as e:
            status_code = getattr(e, "code", None)
            last_exception = e
            if status_code not in RETRYABLE_STATUS_CODES:
                raise
            if attempt == max_retries - 1:
                break
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[retry] Gemini returned {status_code} (attempt {attempt + 1}/{max_retries}), "
                  f"retrying in {delay:.1f}s...")
            time.sleep(delay)
    raise RuntimeError(
        f"Gemini call failed after {max_retries} attempts (transient errors)."
    ) from last_exception

SUMMARY_PROMPT = """\
You are analyzing a meeting transcript. Read it carefully and produce:

1. A concise summary paragraph of what was discussed.
2. A list of concrete decisions made (skip vague statements - only actual decisions).
3. A list of action items, each with a task. Only include an assignee or deadline
   if one was explicitly stated in the meeting - do not invent or infer one.
4. Agenda status: for each agenda item provided below, classify it as covered,
   partially covered, or not covered based on the discussion, with brief
   supporting evidence (a short quote or paraphrase). Leave evidence empty if
   not covered. If no agenda was provided, return an empty list.

Agenda:
{agenda}

Transcript:
{transcript}
"""

def _format_agenda(agenda_items: list[str] | None) -> str:
    """
    Formats a list of agenda item strings into a numbered block for the prompt.
    Returns a placeholder string if no agenda was provided.
    """
    if not agenda_items:
        return "(none provided)"
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(agenda_items))

def extract_meeting_summary(transcript: str, agenda_items: list[str] | None = None) -> MeetingSummary:
    prompt = SUMMARY_PROMPT.format(
        agenda=_format_agenda(agenda_items),
        transcript=transcript
    )
    response = _call_gemini_with_retry(prompt)
    return MeetingSummary.model_validate_json(response.text)  # Safety Net: don't just trust Gemini's schema adherence

if __name__ == "__main__":
    sample_transcript = "PASTE A REAL CLEANED TRANSCRIPT HERE"
    result = extract_meeting_summary(sample_transcript)
    print(result.model_dump_json(indent=2))