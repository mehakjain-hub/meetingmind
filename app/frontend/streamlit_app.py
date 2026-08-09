import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.frontend.utils.theme import (
    inject_theme, render_waveform_meter, render_idle_meter, render_stats_strip, ensure_session_defaults,
)
from app.db.crud import get_meeting_history
from app.db.session import session_scope

st.set_page_config(page_title="MeetingMind", layout="wide")
inject_theme()
ensure_session_defaults()

with session_scope() as session:
    meeting_count = len(get_meeting_history(session))

st.markdown(
    """
    <div class="mm-eyebrow">// audio intelligence pipeline</div>
    """,
    unsafe_allow_html=True,
)
st.title("MeetingMind")
st.caption("Upload a meeting recording → get structured minutes.")
st.markdown(render_idle_meter(), unsafe_allow_html=True)
st.markdown(render_stats_strip(meeting_count), unsafe_allow_html=True)
st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div class="mm-card" style="border-radius:6px 6px 0 0; margin-bottom:0;">'
        '<div class="mm-card-main">Upload</div>'
        '<div style="color:#8B929A; font-size:0.85rem;">Run the pipeline on a new recording.</div>'
        '</div>', unsafe_allow_html=True,
    )
    st.page_link("pages/1_upload.py", label="Open →")
with col2:
    st.markdown(
        '<div class="mm-card" style="border-radius:6px 6px 0 0; margin-bottom:0;">'
        '<div class="mm-card-main">Results</div>'
        '<div style="color:#8B929A; font-size:0.85rem;">Summary, decisions, action items, agenda status.</div>'
        '</div>', unsafe_allow_html=True,
    )
    st.page_link("pages/2_results.py", label="Open →")
with col3:
    st.markdown(
        '<div class="mm-card" style="border-radius:6px 6px 0 0; margin-bottom:0;">'
        '<div class="mm-card-main">History</div>'
        '<div style="color:#8B929A; font-size:0.85rem;">Browse every meeting you\'ve processed.</div>'
        '</div>', unsafe_allow_html=True,
    )
    st.page_link("pages/3_history.py", label="Open →")