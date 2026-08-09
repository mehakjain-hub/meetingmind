from datetime import datetime, timezone
from sqlalchemy import (Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean)
from sqlalchemy.orm import relationship
from app.db.session import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    audio_filename = Column(String(255))
    duration_seconds = Column(Float)
    agenda_text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    transcript = relationship("Transcript", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, unique=True)
    raw_text = Column(Text) # merged, speaker-labeled transcript
    cleaned_text = Column(Text) # after filler-word/punctuation-cleaning
    language = Column(String(10), default="en")
    meeting = relationship("Meeting", back_populates="transcript")

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, unique=True)
    summary_text = Column(Text)
    decisions = Column(Text)
    agenda_status = Column(Text)
    meeting = relationship("Meeting", back_populates="summary")

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    assignee = Column(String(255))
    task = Column(Text, nullable=False)
    deadline = Column(String(100)) # keep as string unless want strict date parsing from LLM output
    is_completed = Column(Boolean, default=False)
    meeting = relationship("Meeting", back_populates="action_items")