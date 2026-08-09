import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.crud import get_meeting_history
from app.db.session import session_scope
from app.frontend.utils.theme import inject_theme, ensure_session_defaults

inject_theme()
ensure_session_defaults()
st.header("History")

with session_scope() as session:
    meetings = get_meeting_history(session)
    rows = [
        {
            "id": m.id,
            "title": m.title,
            "created_at": m.created_at,
            "duration_seconds": m.duration_seconds,
            "agenda_text": m.agenda_text,
        }
        for m in meetings
    ]

if not rows:
    st.write("No meetings yet — run the pipeline from the Upload page.")
else:
    for row in rows:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f'<div class="mm-card-main" style="margin-bottom:2px;">{row["title"]}</div>', unsafe_allow_html=True)
                if row["agenda_text"]:
                    st.caption(f"Agenda: {row['agenda_text']}")
            with col2:
                tags = []
                if row["created_at"]:
                    tags.append(f'<span class="mm-tag">{row["created_at"].strftime("%Y-%m-%d %H:%M")}</span>')
                if row["duration_seconds"]:
                    tags.append(f'<span class="mm-tag">{row["duration_seconds"]:.0f}s</span>')
                st.markdown(f'<div class="mm-card-meta">{"".join(tags)}</div>', unsafe_allow_html=True)
            with col3:
                if st.button("View", key=f"view_{row['id']}"):
                    st.session_state.meeting_id = row["id"]
                    st.session_state.pop("results_data", None)  # clear stale results from a previous meeting
                    st.switch_page("pages/2_results.py")