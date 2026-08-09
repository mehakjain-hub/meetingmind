"""
Each function takes a session (caller manages the session_scope context) and does exactly one insert
or one query. Pipeline/business logic stays out of this file.
"""

import json
from app.db.models import Meeting, Transcript, Summary, ActionItem
from sqlalchemy.orm import joinedload

def create_meeting(session, title, audio_filename=None, duration_seconds=None, agenda_text=None):
    """
    Insert a new meeting row. Flushes (not commits) so the caller gets back
    a populated meeting.id — needed as a foreign key before inserting the
    transcript or anything else — without ending the surrounding
    session_scope() transaction. The whole meeting's writes (meeting,
    transcript, summary, action_items) commit or roll back together when
    the caller's `with session_scope() as session:` block exits, so a
    failure partway through (e.g. a bad extraction response) doesn't leave
    an orphan meeting row with no summary.
    """
    meeting = Meeting(
        title=title,
        audio_filename=audio_filename,
        duration_seconds=duration_seconds,
        agenda_text=agenda_text,
    )
    session.add(meeting)
    session.flush()  # flush, not commit — populates meeting.id, keeps txn open
    session.refresh(meeting)
    return meeting

def save_transcript(session, meeting_id, raw_text, cleaned_text=None, language="en"):
    """
    Insert a transcript row linked to an existing meeting_id.
    Assumes create_meeting() has already been called (flushed) in the same
    session — the row isn't durable until the caller's session_scope()
    commits.
    """
    transcript = Transcript(
        meeting_id=meeting_id,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        language=language,
    )
    session.add(transcript)
    session.flush()
    session.refresh(transcript)
    return transcript

def get_meeting_history(session):
    """
    Return all meetings, most recent first. Used by the future history page.
    """
    return session.query(Meeting).order_by(Meeting.created_at.desc()).all()

def get_meeting_detail(session, meeting_id):
    """
    Fetch one meeting with transcript, summary, and action_items eager-loaded
    so the caller can read them after session_scope() has exited.
    """
    return (
        session.query(Meeting)
        .options(
            joinedload(Meeting.transcript),
            joinedload(Meeting.summary),
            joinedload(Meeting.action_items),
        )
        .filter(Meeting.id == meeting_id)
        .first()
    )

def save_summary(session, meeting_id, summary_text, decisions, agenda_status):
    """
    Insert a summary row linked to an existing meeting_id.
    decisions and agenda_status are stored as JSON strings.
    Flushes only — see create_meeting() for why.
    """
    summary = Summary(
        meeting_id=meeting_id,
        summary_text=summary_text,
        decisions=json.dumps(decisions),
        agenda_status=json.dumps(agenda_status),
    )
    session.add(summary)
    session.flush()
    session.refresh(summary)
    return summary

def save_action_items(session, meeting_id, action_items):
    """
    Bulk insert action items linked to an existing meeting_id.
    action_items is a list of dicts with task/assignee/deadline keys.
    Flushes only — see create_meeting() for why.
    """
    rows = [
        ActionItem(
            meeting_id=meeting_id,
            task=item["task"],
            assignee=item.get("assignee"),
            deadline=item.get("deadline"),
        )
        for item in action_items
    ]
    session.add_all(rows)
    session.flush()
    return rows