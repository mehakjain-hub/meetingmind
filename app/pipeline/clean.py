"""
clean.py - Transcript cleaner

Takes speaker-labeled turns (output pf merge.py) and cleans them up:
- strips filler words (um, uh, like, you know, etc.)
- fixes spacing/punctuation left over from filler removal
- capitalizes first letter of each turn, ensures terminal punctuation

Usage:
    from clean import clean_turns
    cleaned = clean_turns(merged_turns)
"""

import re
import argparse
import json

# Common filler words/phrases. Word-boundary matched, case-insensitive.
# Order matters slightly for multi-word phrases (match before single words).

FILLER_PATTERNS = [
    r"\byou know\b",
    r"\bi mean\b",
    r"\bsort of\b",
    r"\bkind of\b",
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\blike\b",
    r"\bactually\b",
    r"\bbasically\b",
    r"\bliterally\b",
]

FILLER_REGEX = re.compile("|".join(FILLER_PATTERNS), flags=re.IGNORECASE)

# Collapses repeated whitespace
WHITESPACE_REGEX = re.compile(r"\s+")

# Fixes " ," or " ." (space before punctuation) left after filler removal
SPACE_BEFORE_PUNCT_REGEX = re.compile(r"\s+([,.!?])")

# Collapses repeated punctuation (e.g. ",," or ". .")
REPEATED_PUNCT_REGEX = re.compile(r"([,.!?])\s*\1+")

def remove_fillers(text: str) -> str:
    text = FILLER_REGEX.sub("", text)
    text = SPACE_BEFORE_PUNCT_REGEX.sub(r"\1", text)
    text = REPEATED_PUNCT_REGEX.sub(r"\1", text)
    text = WHITESPACE_REGEX.sub(" ", text).strip()
    return text

def fix_punctuation(text: str) -> str:
    if not text:
        return text
    # capitalize first letter
    text = text[0].upper() + text[1:]
    # ensure terminal punctuation
    if text[-1] not in ".!?":
        text += "."
    return text

def clean_text(text: str) -> str:
    text = remove_fillers(text)
    text = fix_punctuation(text)
    return text

def clean_turns(turns: list[dict], text_key: str = "text") -> list[dict]:
    """
    turns: list of dicts, each with at least a text_key field (default "text").
    Returns a new list with cleaned text; other fields (speaker, start, end) preserved.
    """
    cleaned = []
    for turn in turns:
        new_turn = dict(turn)
        raw = turn.get(text_key, "")
        new_turn[text_key] = clean_text(raw)
        cleaned.append(new_turn)
    return cleaned

def main():
    parser = argparse.ArgumentParser(description="Clean a merged transcription JSON file.")
    parser.add_argument("input", help="Path to merged transcript JSON (list of turns.)")
    parser.add_argument("-o", "--output", help="Path to write cleaned JSON", default=None)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        turns = json.load(f)

    cleaned = clean_turns(turns)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)
        print(f"Wrote cleaned transcript to {args.output}")
    else:
        print(json.dumps(cleaned, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()