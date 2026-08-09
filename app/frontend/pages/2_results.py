import json
import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.crud import get_meeting_detail
from app.db.session import session_scope
from app.frontend.utils.theme import inject_theme, render_action_item_card, render_generic_card, ensure_session_defaults

inject_theme()
ensure_session_defaults()
st.header("Results")

# meeting_id comes from the just-finished upload run if there is one;
# otherwise let the person type one in (e.g. arriving here directly,
# or from a future history page link).

default_id = st.session_state.get("meeting_id")
meeting_id = st.number_input("Meeting ID", min_value=1, step=1, value=default_id if default_id else 1,)
arrived_from_history = default_id is not None and "results_data" not in st.session_state
if st.button("Load") or arrived_from_history:
    with session_scope() as session:
        detail = get_meeting_detail(session, meeting_id=meeting_id)
        if detail is None:
            st.error(f"No meeting found with id {meeting_id}.")
            st.stop()
        title = detail.title
        duration_seconds = detail.duration_seconds
        agenda_text = detail.agenda_text
        cleaned_transcript = detail.transcript.cleaned_text if detail.transcript else None
        raw_transcript = detail.transcript.raw_text if detail.transcript else None
        summary_text = detail.summary.summary_text if detail.summary else None
        decisions = json.loads(detail.summary.decisions) if detail.summary and detail.summary.decisions else []
        agenda_status = json.loads(detail.summary.agenda_status) if detail.summary and detail.summary.agenda_status else []
        action_items = [
            {"task": ai.task, "assignee": ai.assignee, "deadline": ai.deadline}
            for ai in (detail.action_items or [])
        ]
    st.session_state.results_data = {
        "title": title,
        "duration_seconds": duration_seconds,
        "agenda_text": agenda_text,
        "cleaned_transcript": cleaned_transcript,
        "raw_transcript": raw_transcript,
        "summary_text": summary_text,
        "decisions": decisions,
        "agenda_status": agenda_status,
        "action_items": action_items,
    }
if "results_data" in st.session_state:
    data = st.session_state.results_data
    st.subheader(data["title"] or "Untitled Meeting")
    if data["duration_seconds"]:
        st.caption(f"Duration: {data['duration_seconds']:.1f}s")
    st.markdown("### Summary")
    st.write(data["summary_text"] or "_No summary available._")
    st.markdown("### Decisions")
    if data["decisions"]:
        for d in data["decisions"]:
            st.markdown(render_generic_card(d), unsafe_allow_html=True)
    else:
        st.write("_No decisions extracted._")
    st.markdown("### Action Items")
    if data["action_items"]:
        for ai in data["action_items"]:
            st.markdown(
                render_action_item_card(ai["task"], ai.get("assignee"), ai.get("deadline")),
                unsafe_allow_html=True,
            )
    else:
        st.write("_No action items extracted._")
    st.markdown("### Agenda Status")
    if data["agenda_text"]:
        if data["agenda_status"]:
            for a in data["agenda_status"]:
                # status_key guess: adjust to your actual AgendaStatus field name
                # if it isn't "status" or "covered" — the card still renders fine
                # either way, just without the color coding.
                st.markdown(render_generic_card(a, status_key="status"), unsafe_allow_html=True)
        else:
            st.write("_No agenda status extracted._")
    else:
        st.write("_No agenda was provided for this meeting._")
    with st.expander("Cleaned transcript"):
        st.text(data["cleaned_transcript"] or "")
    with st.expander("Raw transcript"):
        st.text(data["raw_transcript"] or "")