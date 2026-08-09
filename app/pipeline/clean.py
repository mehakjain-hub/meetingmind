"""
Takes speaker-labeled turns (output pf merge.py) and cleans them up:
- strips filler words (um, uh, like, you know, etc.)
- fixes spacing/punctuation left over from filler removal
- capitalizes first letter of each turn, ensures terminal punctuation
"""

import re
import argparse
import json

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

# Collapses a run of punctuation marks (possibly mixed, e.g. ", ." or ",,")
# left adjacent after filler removal into a single mark. When the run mixes
# marks, keep the strongest terminal-ish one (. ! ? outrank ,) so we don't
# downgrade "!" or "?" to a comma.
PUNCT_RUN_REGEX = re.compile(r"[,.!?](?:\s*[,.!?])+")
_PUNCT_STRENGTH = {",": 0, ".": 1, "!": 1, "?": 1}

def _collapse_punct_run(match: re.Match) -> str:
    marks = [c for c in match.group(0) if c in ".,!?"]
    strongest = max(marks, key=lambda c: _PUNCT_STRENGTH[c])
    return strongest

# Stray punctuation stranded at the very start/end of a turn (e.g. a filler
# word that opened or closed the sentence leaves ", " at the front, or a
# trailing ", " with nothing after it once the filler is gone).
LEADING_PUNCT_REGEX = re.compile(r"^\s*[,.!?]+\s*")
TRAILING_PUNCT_REGEX = re.compile(r"\s*[,.!?]+\s*$")

def remove_fillers(text: str) -> str:
    text = FILLER_REGEX.sub("", text)
    text = SPACE_BEFORE_PUNCT_REGEX.sub(r"\1", text)
    text = PUNCT_RUN_REGEX.sub(_collapse_punct_run, text)
    text = WHITESPACE_REGEX.sub(" ", text).strip()
    text = LEADING_PUNCT_REGEX.sub("", text)
    text = TRAILING_PUNCT_REGEX.sub("", text)
    return text

def fix_punctuation(text: str) -> str:
    if not text:
        return text
    # capitalize first letter
    text = text[0].upper() + text[1:]
    # ensure terminal punctuation (text is already stripped of trailing
    # stray commas/marks by remove_fillers, so this only adds one, never
    # stacks onto a leftover comma like "word,.")
    if text[-1] not in ".!?":
        text += "."
    return text

def clean_text(text: str) -> str:
    text = remove_fillers(text)
    text = fix_punctuation(text)
    return text

def clean_turns(turns: list[dict], text_key: str = "text") -> list[dict]:
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