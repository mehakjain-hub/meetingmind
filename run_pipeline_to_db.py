"""
run_pipeline_to_db.py - Day 18 end-to-end driver.

Runs the full MeetingMind pipeline on one audio file, extracts structured
summary/decisions/action-items/agenda-status via Gemini, and persists
everything to Postgres via crud.py, then reads it back to confirm the
round trip worked.

Usage:
    python run_pipeline_to_db.py path/to/audio.wav --title "Team Standup"
    python run_pipeline_to_db.py path/to/audio.wav --title "Team Standup" --agenda "Discuss Q3 roadmap; review budget"

NOTE: language defaults to None (auto-detect) both here and in transcribe_audio().
Pass --language explicitly (e.g. --language en) to force a language instead.
"""

import argparse
import sys
from pathlib import Path
from app.db.crud import (
    create_meeting,
    save_transcript,
    save_summary,
    save_action_items,
    get_meeting_detail,
)
from app.pipeline.preprocess import preprocess_audio
from app.pipeline.transcribe import transcribe_audio
from app.pipeline.align import align
from app.pipeline.diarize import diarize
from app.pipeline.merge import merge_transcript_with_speakers
from app.pipeline.clean import clean_turns
from app.pipeline.extract import extract_meeting_summary
from app.db.session import session_scope

def turns_to_text(turns: list[dict]) -> str:
    # Format speaker-labeled turns into a single readable transcript string.
    lines = [f"Speaker {t['speaker']}: {t['text']}" for t in turns]
    return "\n".join(lines)

def run_pipeline(
    raw_audio_path: str,
    title: str,
    model_size: str = "small",
    language: str | None = None,
    agenda: str | None = None,
):
    print(f"\n[1/6] Preprocessing: {raw_audio_path}")
    wav_path = preprocess_audio(raw_audio_path)

    print(f"[2/6] Transcribing with faster-whisper ({model_size})")
    whisper_segments, detected_language = transcribe_audio(wav_path, model_size, language)

    print(f"[3/6] Aligning with WhisperX")
    aligned_segments = align(wav_path, whisper_segments, detected_language)

    print(f"[4/6] Diarizing with pyannote")
    diarization_segments = diarize(wav_path)

    print(f"[5/6] Merging transcript + speakers")
    turns = merge_transcript_with_speakers(aligned_segments, diarization_segments)
    cleaned_turns = clean_turns(turns)

    raw_text = turns_to_text(turns)
    cleaned_text = turns_to_text(cleaned_turns)

    duration_seconds = max((t["end"] for t in turns), default=0.0)

    print(f"[6/6] Extracting summary, decisions, action items, agenda status")
    result = extract_meeting_summary(cleaned_text, agenda)

    print("\n--- Saving to DB ---")
    with session_scope() as session:
        meeting = create_meeting(
            session,
            title=title,
            audio_filename=Path(raw_audio_path).name,
            duration_seconds=duration_seconds,
            agenda_text=agenda,
        )
        meeting_id = meeting.id

        save_transcript(
            session,
            meeting_id=meeting_id,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            language=detected_language,
        )

        save_summary(
            session,
            meeting_id=meeting_id,
            summary_text=result.summary,
            decisions=[d.model_dump() for d in result.decisions],
            agenda_status=[a.model_dump() for a in result.agenda_status],
        )

        save_action_items(
            session,
            meeting_id=meeting_id,
            action_items=[ai.model_dump() for ai in result.action_items],
        )

        print(f"Saved meeting_id = {meeting_id}")

    print("\n--- Reading back from DB ---")
    with session_scope() as session:
        detail = get_meeting_detail(session, meeting_id=meeting_id)

        print(f"Title: {detail.title}")
        print(f"Duration: {detail.duration_seconds:.2f}s")

        print(f"\nRaw transcript:\n{detail.transcript.raw_text}")
        print(f"\nCleaned transcript:\n{detail.transcript.cleaned_text}")

        print(f"\nSummary:\n{detail.summary.summary_text}")
        print(f"\nDecisions (raw JSON):\n{detail.summary.decisions}")
        print(f"\nAgenda status (raw JSON):\n{detail.summary.agenda_status}")

        print(f"\nAction items ({len(detail.action_items)}):")
        for ai in detail.action_items:
            print(f"  - task={ai.task!r}, assignee={ai.assignee!r}, deadline={ai.deadline!r}")

    return meeting_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full MeetingMind pipeline and save to DB")
    parser.add_argument("audio_path", help="Path to raw meeting audio file")
    parser.add_argument("--title", default="Untitled Meeting", help="Meeting title")
    parser.add_argument("--model_size", default="small")
    parser.add_argument("--language", default=None, help="Force a language code (e.g. 'en', 'hi'). Omit to let Whisper auto-detect.")
    parser.add_argument("--agenda", default=None, help="Agenda text, e.g. 'Discuss Q3 roadmap; review budget'")
    args = parser.parse_args()

    run_pipeline(args.audio_path, args.title, args.model_size, args.language, args.agenda)