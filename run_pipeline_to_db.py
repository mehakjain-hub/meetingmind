"""
run_pipeline_to_db.py - Day 11 end-to-end driver.

Runs the full MeetingMind pipeline on one audio file and persists the
result to Postgres via crud.py, then reads it back to confirm the
round trip worked.

Usage:
    python run_pipeline_to_db.py path/to/audio.wav --title "Team Standup"

NOTE: transcribe_audio() currently discards the detected language
(info.language is printed but not returned). Defaulting to "en" here.
TODO: return info.language from transcribe_audio() and thread it through
align.py / merge.py once this driver is confirmed working, so
Transcript.language reflects actual detection instead of a hardcoded default.
"""

import argparse
import sys
from pathlib import Path
from app.db.crud import create_meeting, save_transcript, get_meeting_detail
from app.pipeline.preprocess import preprocess_audio
from app.pipeline.transcribe import transcribe_audio
from app.pipeline.align import align
from app.pipeline.diarize import diarize
from app.pipeline.merge import merge_transcript_with_speakers
from app.pipeline.clean import clean_turns
from app.db.session import session_scope

def turns_to_text(turns: list[dict]) -> str:
    # Format speaker-labeled turns into a single readable transcript string.
    lines = [f"Speaker {t['speaker']}: {t['text']}" for t in turns]
    return "\n".join(lines)

def run_pipeline(raw_audio_path: str, title: str, model_size: str = "small", language: str = "en"):
    print(f"\n[1/5] Preprocessing: {raw_audio_path}")
    wav_path = preprocess_audio(raw_audio_path)

    print(f"[2/5] Transcribing with faster-whisper ({model_size})")
    whisper_segments, detected_language = transcribe_audio(wav_path, model_size, language)

    print(f"[3/5] Aligning with WhisperX")
    aligned_segments = align(wav_path, whisper_segments, language)

    print(f"[4/5] Diarizing with pyannote")
    diarization_segments = diarize(wav_path)

    print(f"[5/5] Merging transcript + speakers")
    turns = merge_transcript_with_speakers(aligned_segments, diarization_segments)
    cleaned_turns = clean_turns(turns)

    raw_text = turns_to_text(turns)
    cleaned_text = turns_to_text(cleaned_turns)

    duration_seconds = max((t["end"] for t in turns), default=0.0)

    print("\n--- Saving to DB ---")
    with session_scope() as session:
        meeting = create_meeting(
            session,
            title=title,
            audio_filename=Path(raw_audio_path).name,
            duration_seconds=duration_seconds,
        )
        meeting_id = meeting.id
        save_transcript(
            session,
            meeting_id=meeting_id,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            language=detected_language,
        )

        print(f"Saved meeting_id = {meeting_id}")
        print("\n--- Reading back from DB ---")
        with session_scope() as session:
            detail = get_meeting_detail(session, meeting_id=meeting_id)
            print(f"Title: {detail.title}")
            print(f"Duration: {detail.duration_seconds:.2f}s")
            print(f"Raw transcript:\n{detail.transcript.raw_text}")
            print(f"\nCleaned transcript:\n{detail.transcript.cleaned_text}")

        return meeting_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full MeetingMind pipeline and save to DB")
    parser.add_argument("audio_path", help="Path to raw meeting audio file")
    parser.add_argument("--title", default="Untitled Meeting", help="Meeting title")
    parser.add_argument("--model_size", default="small")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    run_pipeline(args.audio_path, args.title, args.model_size, args.language)