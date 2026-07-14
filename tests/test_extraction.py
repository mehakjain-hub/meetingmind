# test_extraction.py
# Run from project root: python -m app.pipeline.test_extraction
# (or adjust imports below if your run context differs)
#
# Runs the full pipeline (preprocess -> transcribe -> align -> diarize -> merge -> clean)
# on a given clip, formats the cleaned turns into a flat transcript, then feeds it into
# extract_meeting_summary() and prints the result.

from app.pipeline.preprocess import preprocess_audio
from app.pipeline.transcribe import transcribe_audio
from app.pipeline.align import align
from app.pipeline.diarize import diarize
from app.pipeline.merge import merge_transcript_with_speakers
from app.pipeline.clean import clean_turns
from app.pipeline.extract import extract_meeting_summary


def format_transcript(turns: list[dict]) -> str:
    """
    Flattens cleaned speaker turns into a plain-text transcript
    suitable for the extraction prompt, e.g.:
        Speaker SPEAKER_00: Let's start with the budget review.
        Speaker SPEAKER_01: Sounds good, I'll pull up the numbers.
    """
    lines = []
    for turn in turns:
        speaker = turn.get("speaker", "UNKNOWN")
        text = turn.get("text", "").strip()
        if text:
            lines.append(f"Speaker {speaker}: {text}")
    return "\n".join(lines)


def run_full_pipeline(audio_path: str, agenda: str | None = None):
    print(f"\n{'='*60}")
    print(f"Processing: {audio_path}")
    print(f"{'='*60}")

    preprocessed_path = preprocess_audio(audio_path)

    raw_segments, detected_language = transcribe_audio(
        preprocessed_path, model_size="small", language="en"
    )
    print(f"Detected language: {detected_language}")

    aligned_segments = align(preprocessed_path, raw_segments, language_code="en")
    diarization_segments = diarize(preprocessed_path)
    merged_turns = merge_transcript_with_speakers(aligned_segments, diarization_segments)
    cleaned_turns = clean_turns(merged_turns)

    transcript_text = format_transcript(cleaned_turns)

    print("\n--- CLEANED TRANSCRIPT (first 800 chars) ---")
    print(transcript_text[:800])

    result = extract_meeting_summary(transcript_text, agenda=agenda)

    print("\n--- EXTRACTED MEETING SUMMARY ---")
    print(result.model_dump_json(indent=2))

    return transcript_text, result


if __name__ == "__main__":
    clips = [
        "/Users/mehakjain/meetingmind/sample_data/meeting-clip2 (1 speaker).wav",
        "/Users/mehakjain/meetingmind/sample_data/meeting-clip1 (2 speakers)_16k_mono.wav",
    ]

    for clip in clips:
        try:
            run_full_pipeline(clip)
        except Exception as e:
            print(f"\n[ERROR] Failed on {clip}: {e}")