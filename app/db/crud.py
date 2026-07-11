"""
app/db/crud.py - Single-purpose DB operations for MeetingMind.

Each function takes a session (caller manages the session_scope context)
and does exactly one insert or one query. Pipeline/business logic stays
out of this file.
"""

from app.db.models import Meeting, Transcript
from sqlalchemy.orm import joinedload

def create_meeting(session, title, audio_filename=None, duration_seconds=None, agenda_text=None):
    """
    Insert a new meeting row. Commits immediately so the caller gets back
    a populated meeting.id — needed as a foreign key before inserting the
    transcript or anything else.
    """
    meeting = Meeting(
        title=title,
        audio_filename=audio_filename,
        duration_seconds=duration_seconds,
        agenda_text=agenda_text,
    )
    session.add(meeting)
    session.commit()  # commit here, not just flush — we need meeting.id populated
    session.refresh(meeting)
    return meeting

def save_transcript(session, meeting_id, raw_text, cleaned_text=None, language="en"):
    """
    Insert a transcript row linked to an existing meeting_id.
    Assumes create_meeting() has already been called and committed.
    """
    transcript = Transcript(
        meeting_id=meeting_id,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        language=language,
    )
    session.add(transcript)
    session.commit()
    session.refresh(transcript)
    return transcript

def get_meeting_history(session):
    """
    Return all meetings, most recent first. Used by the future history page.
    """
    return session.query(Meeting).order_by(Meeting.created_at.desc()).all()

def get_meeting_detail(session, meeting_id):
    return (session.query(Meeting).options(joinedload(Meeting.transcript)).filter(Meeting.id == meeting_id).first())