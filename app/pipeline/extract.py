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
   If no concrete action items were discussed, return an empty list -
   do not invent one to fill the response.
4. Agenda status: for each agenda item provided below, classify it as covered,
   partially covered, or not covered based on the discussion, with brief
   supporting evidence (a short quote or paraphrase). Leave evidence empty if
   not covered. If no agenda was provided, return an empty list.

Agenda:
{agenda}

Transcript:
{transcript}
"""

MAX_WORDS_PER_CHUNK = 4500 # ~6000 tokens, conservative for gemini-3.5-flash context
CHUNK_OVERLAP_WORDS = 200 # keeps context like "as I mentioned earlier" from being lost across chunk boundaries

REDUCE_PROMPT = """\
You are consolidating notes from a long meeting that was processed in {n} parts.
Below are partial summaries, decisions, and action items extracted from each part,
in order. Merge them into a single coherent output:

1. One concise overall summary paragraph (don't just concatenate the partial ones).
2. A deduplicated list of decisions (merge near-duplicates across parts).
3. A deduplicated list of action items (merge near-duplicates across parts).
4. Agenda status: classify each agenda item as covered/partially covered/not covered
   using evidence from anywhere in the parts below. If no agenda was provided,
   return an empty list.

Agenda:
{agenda}

Partial extractions:
{partial_notes}
"""

def _format_agenda(agenda_items: list[str] | None) -> str:
    """
    Formats a list of agenda item strings into a numbered block for the prompt.
    Returns a placeholder string if no agenda was provided.
    """
    if not agenda_items:
        return "(none provided)"
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(agenda_items))

def _chunk_transcript(transcript: str, max_words: int = MAX_WORDS_PER_CHUNK,
                      overlap_words: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    words = transcript.split()
    if len(words) <= max_words:
        return [transcript]
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap_words
    return chunks

def _reduce_chunks(agenda_items: list[str] | None, chunk_results: list[MeetingSummary]) -> MeetingSummary:
    partial_notes = "\n\n".join(
        f"--- Part {i+1} ---\n"
        f"Summary: {r.summary}\n"
        f"Decisions: {[d.model_dump() for d in r.decisions]}\n"
        f"Action items: {[a.model_dump() for a in r.action_items]}"
        for i, r in enumerate(chunk_results)
    )
    prompt = REDUCE_PROMPT.format(
        n = len(chunk_results),
        agenda = _format_agenda(agenda_items),
        partial_notes = partial_notes,
    )
    response = _call_gemini_with_retry(prompt)
    return MeetingSummary.model_validate_json(response.text)

def extract_meeting_summary(transcript: str, agenda_items: list[str] | None = None) -> MeetingSummary:
    chunks = _chunk_transcript(transcript)
    if len(chunks) == 1:
        prompt = SUMMARY_PROMPT.format(
            agenda=_format_agenda(agenda_items),
            transcript=chunks[0]
        )
        response = _call_gemini_with_retry(prompt)
        return MeetingSummary.model_validate_json(response.text)

    # map: extract per chunk (skip agenda check per-chunk, only apply it in the reduce step
    # since a single chunk rarely has the full context to judge "covered" fairly)
    chunk_results = []
    for chunk in chunks:
        prompt = SUMMARY_PROMPT.format(agenda = "(none provided)", transcript=chunk)
        response = _call_gemini_with_retry(prompt)
        chunk_results.append(MeetingSummary.model_validate_json(response.text))

    # reduce: consolidate + apply the real agenda check across all parts
    return _reduce_chunks(agenda_items, chunk_results)

if __name__ == "__main__":
    sample_transcript = "PASTE A REAL CLEANED TRANSCRIPT HERE"
    result = extract_meeting_summary(sample_transcript)
    print(result.model_dump_json(indent=2))