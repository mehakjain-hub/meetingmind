"""
Shared visual theme for MeetingMind's Streamlit frontend.

Design direction: a physical rack-mount hardware unit. Brushed-steel
panels, rivets, silkscreened mono labels, a real segmented VU-meter for
pipeline progress, and the sidebar/background/widget chrome themed to
match — not just isolated components.

Call inject_theme() once at the top of every page.
"""

import streamlit as st

# --- token system ---
RACK = "#0C0F12"        # page background — gunmetal near-black
PANEL = "#1A1F24"       # card / surface background — brushed steel panel
STEEL = "#333B42"       # borders, dividers, rivets
PAPER = "#E4E7EA"       # primary text — cool off-white
SIGNAL = "#3FBF7F"      # primary accent — VU-meter green (done / good)
DATA = "#5B9DD9"        # secondary accent — instrument blue (peak / data)
ERROR = "#D9534F"       # errors only — never used for normal states
SEG_COUNT = 5           # segments per meter column

_SESSION_DEFAULTS = {
    "pipeline_status": "idle",
    "meeting_id": None,
    "raw_turns": None,
    "cleaned_turns": None,
    "error_message": None,
}

def ensure_session_defaults():
    for key, val in _SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val

def inject_theme():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'IBM Plex Sans', sans-serif;
        }}
        h1, h2, h3 {{
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em;
        }}
        code, .mm-mono {{
            font-family: 'IBM Plex Mono', monospace !important;
        }}

        /* --- whole-app background: brushed metal, not flat --- */
        [data-testid="stAppViewContainer"] {{
            background:
                repeating-linear-gradient(115deg, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 1px, transparent 1px, transparent 3px),
                radial-gradient(ellipse at top left, #16191D 0%, {RACK} 60%);
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}

        /* --- sidebar --- */
        [data-testid="stSidebar"] {{
            background: {PANEL};
            border-right: 1px solid {STEEL};
        }}
        [data-testid="stSidebarNavItems"] a {{
            font-family: 'IBM Plex Mono', monospace !important;
            font-size: 0.78rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #8B929A !important;
            border-left: 2px solid transparent;
            padding-left: 10px !important;
        }}
        [data-testid="stSidebarNavItems"] a:hover {{
            color: {PAPER} !important;
            border-left: 2px solid {DATA};
            background: rgba(91, 157, 217, 0.08) !important;
        }}
        [data-testid="stSidebarNavItems"] a[aria-current="page"] {{
            color: {SIGNAL} !important;
            border-left: 2px solid {SIGNAL};
            background: rgba(63, 191, 127, 0.08) !important;
        }}

        /* silkscreened panel-label look for section headers */
        .mm-eyebrow {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #6B7480;
            margin-bottom: 2px;
        }}

        /* speaker chips */
        .mm-chip {{
            display: inline-block;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            padding: 1px 8px;
            border-radius: 3px;
            margin-right: 6px;
            letter-spacing: 0.02em;
        }}

        /* --- widget chrome --- */
        .stButton > button {{
            font-family: 'IBM Plex Mono', monospace;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            font-size: 0.8rem;
            border: 1px solid {STEEL};
            border-radius: 4px;
        }}
        .stButton > button[kind="primary"] {{
            background: {SIGNAL};
            border: none;
            color: #06120B;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: #35A86E;
        }}
        .stButton > button[kind="secondary"]:hover {{
            border-color: {DATA};
            color: {DATA};
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: {PANEL} !important;
            border: 1px dashed {STEEL} !important;
            border-radius: 6px !important;
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input {{
            background: {PANEL} !important;
            border: 1px solid {STEEL} !important;
            color: {PAPER} !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }}
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {{
            border-color: {DATA} !important;
            box-shadow: 0 0 0 1px {DATA}55 !important;
        }}
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            background: {PANEL} !important;
            border-color: {STEEL} !important;
        }}
        [data-testid="stRadio"] label span:first-child {{
            border-color: {STEEL} !important;
        }}
        [data-testid="stRadio"] label[data-checked="true"] span:first-child {{
            background: {SIGNAL} !important;
            border-color: {SIGNAL} !important;
        }}
        [data-testid="stExpander"] {{
            background: {PANEL} !important;
            border: 1px solid {STEEL} !important;
            border-radius: 6px !important;
        }}

        /* --- VU-meter pipeline progress --- */
        .mm-rack {{
            background: linear-gradient(180deg, #171B1F 0%, #101317 100%);
            border: 1px solid {STEEL};
            border-radius: 6px;
            padding: 18px 20px 14px 20px;
            margin: 1rem 0 0.75rem 0;
            position: relative;
        }}
        .mm-rack::before, .mm-rack::after {{
            content: "";
            position: absolute;
            top: 8px;
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #444C54;
            box-shadow: inset 0 1px 1px rgba(0,0,0,0.6), 0 0 0 1px {RACK};
        }}
        .mm-rack::before {{ left: 8px; }}
        .mm-rack::after {{ right: 8px; }}

        .mm-meter {{
            display: flex;
            gap: 10px;
            align-items: flex-end;
            height: 56px;
        }}
        .mm-col {{
            flex: 1;
            display: flex;
            flex-direction: column-reverse;
            gap: 3px;
            height: 100%;
        }}
        .mm-seg {{
            flex: 1;
            border-radius: 1px;
            background: #262C32;
        }}
        .mm-seg.chase {{ animation: mm-chase 1s ease-in-out infinite; }}
@keyframes mm-chase {{
    0%, 100% {{ opacity: 0.3; }}
    50% {{ opacity: 1; }}
}}
.mm-seg.idle {{ animation: mm-idle 2.6s ease-in-out infinite; }}
@keyframes mm-idle {{
    0%, 100% {{ opacity: 0.25; }}
    50% {{ opacity: 0.6; }}
}}
[data-testid="stPageLink"] {{
    border: 1px solid {STEEL} !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
    background: {PANEL} !important;
    margin-top: -11px !important;
}}
[data-testid="stPageLink"] p {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    color: #8B929A !important;
}}
[data-testid="stPageLink"]:hover p {{ color: {SIGNAL} !important; }}

        .mm-labels {{ display: flex; gap: 10px; margin-top: 8px; }}
        .mm-label {{
            flex: 1;
            text-align: center;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.64rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #565E66;
        }}
        .mm-label.done, .mm-label.active {{ color: {PAPER}; }}
        .mm-label.error {{ color: {ERROR}; }}

        /* --- cards: decisions, action items, agenda status, history rows, nav --- */
        .mm-card {{
            background: {PANEL};
            border: 1px solid {STEEL};
            border-radius: 5px;
            padding: 14px 18px;
            margin-bottom: 10px;
            position: relative;
        }}
        .mm-card::before, .mm-card::after {{
            content: "";
            position: absolute;
            top: 6px;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #40484F;
        }}
        .mm-card::before {{ left: 6px; }}
        .mm-card::after {{ right: 6px; }}
        .mm-card-main {{ font-size: 0.95rem; color: {PAPER}; margin-bottom: 8px; line-height: 1.4; }}
        .mm-card-meta {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .mm-tag {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.02em;
            padding: 2px 8px;
            border-radius: 3px;
            background: rgba(228, 231, 234, 0.06);
            color: #9AA2AA;
            border: 1px solid {STEEL};
        }}
        .mm-tag.status-covered {{ background: {SIGNAL}1A; color: {SIGNAL}; border-color: {SIGNAL}55; }}
        .mm-tag.status-pending {{ background: {DATA}1A; color: {DATA}; border-color: {DATA}55; }}
        .mm-tag.status-partial {{ background: {STEEL}55; color: {PAPER}; border: 1px dashed {STEEL}; }}

        /* --- home page hero + nav cards --- */
        .mm-hero {{
            border: 1px solid {STEEL};
            background: linear-gradient(180deg, #171B1F 0%, #101317 100%);
            border-radius: 8px;
            padding: 32px 36px;
            margin-bottom: 24px;
            position: relative;
        }}
        .mm-hero::before, .mm-hero::after {{
            content: ""; position: absolute; top: 10px; width: 6px; height: 6px;
            border-radius: 50%; background: #444C54;
            box-shadow: inset 0 1px 1px rgba(0,0,0,0.6), 0 0 0 1px {RACK};
        }}
        .mm-hero::before {{ left: 10px; }}
        .mm-hero::after {{ right: 10px; }}
        .mm-nav-grid {{ display: flex; gap: 16px; margin-top: 8px; }}
        .mm-nav-card {{
            flex: 1;
            background: {PANEL};
            border: 1px solid {STEEL};
            border-radius: 6px;
            padding: 20px;
        }}
        .mm-nav-icon {{ margin-bottom: 10px; }}
        .mm-nav-title {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.85rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: {PAPER};
            margin-bottom: 6px;
        }}
        .mm-nav-desc {{ font-size: 0.85rem; color: #8B929A; line-height: 1.4; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

PIPELINE_STAGES = [
    "Preprocess", "Transcribe", "Align", "Diarize",
    "Merge", "Clean", "Extract", "Save",
]

def render_waveform_meter(current_index: int, errored: bool = False) -> str:
    columns = []
    labels = []
    for i, label in enumerate(PIPELINE_STAGES):
        if i < current_index:
            state = "done"
        elif i == current_index:
            state = "error" if errored else "active"
        else:
            state = "pending"
        segs = []
        for s in range(SEG_COUNT):
            is_top = s == SEG_COUNT - 1
            if state == "done":
                segs.append(f'<div class="mm-seg lit-{"blue" if is_top else "green"} steady"></div>')
            elif state == "active":
                cls = f'lit-{"blue" if is_top else "green"} chase'
                segs.append(f'<div class="mm-seg {cls}" style="animation-delay:{s * 0.07:.2f}s"></div>')
            elif state == "error":
                segs.append(f'<div class="mm-seg lit-error chase" style="animation-delay:{s * 0.05:.2f}s"></div>')
            else:
                segs.append('<div class="mm-seg"></div>')

        columns.append(f'<div class="mm-col">{"".join(segs)}</div>')
        label_cls = "error" if state == "error" else ("done" if state in ("done", "active") else "")
        labels.append(f'<div class="mm-label {label_cls}">{label}</div>')
    return (
        f'<div class="mm-rack"><div class="mm-meter">{"".join(columns)}</div></div>'
        f'<div class="mm-labels">{"".join(labels)}</div>'
    )

_SPEAKER_COLORS = [SIGNAL, DATA, "#7FD4B8", "#4E7FB0", "#6FCF97"]

def speaker_chip_html(speaker_label: str) -> str:
    idx = hash(speaker_label) % len(_SPEAKER_COLORS)
    color = _SPEAKER_COLORS[idx]
    return (
        f'<span class="mm-chip" style="background:{color}22; color:{color}; '
        f'border:1px solid {color}55;">{speaker_label}</span>'
    )

def render_action_item_card(task: str, assignee: str | None, deadline: str | None) -> str:
    tags = []
    if assignee:
        tags.append(f'<span class="mm-tag">@ {assignee}</span>')
    if deadline:
        tags.append(f'<span class="mm-tag">due {deadline}</span>')
    tags_html = "".join(tags) if tags else '<span class="mm-tag">unassigned</span>'
    return (
        f'<div class="mm-card"><div class="mm-card-main">{task}</div>'
        f'<div class="mm-card-meta">{tags_html}</div></div>'
    )

def render_generic_card(item: dict, status_key: str | None = None) -> str:
    if not item:
        return '<div class="mm-card"><div class="mm-card-main">—</div></div>'
    keys = list(item.keys())
    main_key = keys[0]
    main_value = item.get(main_key, "")
    tags = []
    for k in keys[1:]:
        v = item.get(k)
        if v is None or v == "":
            continue
        cls = "mm-tag"
        if status_key and k == status_key:
            v_norm = str(v).lower().strip()
            if v_norm in ("covered", "true", "done", "yes"):
                cls += " status-covered"
            elif v_norm in ("partially_covered", "partial"):
                cls += " status-partial"
            elif v_norm in ("not_covered", "false", "no", "pending"):
                cls += " status-pending"
        tags.append(f'<span class="{cls}">{k}: {v}</span>')
    return (
        f'<div class="mm-card"><div class="mm-card-main">{main_value}</div>'
        f'<div class="mm-card-meta">{"".join(tags)}</div></div>'
    )

# --- home page hero + nav cards ---
_ICON_WAVEFORM = f'''<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{SIGNAL}" stroke-width="2" stroke-linecap="round"><line x1="3" y1="12" x2="3" y2="12"/><line x1="7" y1="7" x2="7" y2="17"/><line x1="11" y1="4" x2="11" y2="20"/><line x1="15" y1="8" x2="15" y2="16"/><line x1="19" y1="10" x2="19" y2="14"/><line x1="21" y1="12" x2="21" y2="12"/></svg>'''
_ICON_CHECKLIST = f'''<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{DATA}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l2 2 4-4"/><rect x="3" y="3" width="18" height="18" rx="2"/></svg>'''
_ICON_CLOCK = f'''<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{SIGNAL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>'''

def render_home() -> str:
    return f"""
    <div class="mm-hero">
        <div class="mm-eyebrow">// audio intelligence pipeline</div>
        <h1 style="margin:6px 0 4px 0;">MeetingMind</h1>
        <div style="color:#8B929A; font-size:0.95rem;">Upload a meeting recording → get structured minutes.</div>
        <div class="mm-nav-grid">
            <div class="mm-nav-card">
                <div class="mm-nav-icon">{_ICON_WAVEFORM}</div>
                <div class="mm-nav-title">Upload</div>
                <div class="mm-nav-desc">Run the pipeline on a new recording — transcribe, diarize, extract.</div>
            </div>
            <div class="mm-nav-card">
                <div class="mm-nav-icon">{_ICON_CHECKLIST}</div>
                <div class="mm-nav-title">Results</div>
                <div class="mm-nav-desc">Summary, decisions, action items, and agenda coverage.</div>
            </div>
            <div class="mm-nav-card">
                <div class="mm-nav-icon">{_ICON_CLOCK}</div>
                <div class="mm-nav-title">History</div>
                <div class="mm-nav-desc">Browse and revisit every meeting you've processed.</div>
            </div>
        </div>
    </div>
    """

# --- idle ambient meter (shown on the home page, before any pipeline runs) ---
def render_idle_meter() -> str:
    columns = []
    labels = []
    for i, label in enumerate(PIPELINE_STAGES):
        segs = []
        for s in range(SEG_COUNT):
            if s == 0:
                segs.append(f'<div class="mm-seg lit-green idle" style="animation-delay:{i * 0.15:.2f}s"></div>')
            else:
                segs.append('<div class="mm-seg"></div>')
        columns.append(f'<div class="mm-col">{"".join(segs)}</div>')
        labels.append(f'<div class="mm-label">{label}</div>')
    return (
        f'<div class="mm-rack"><div class="mm-meter">{"".join(columns)}</div></div>'
        f'<div class="mm-labels">{"".join(labels)}</div>'
    )

def render_stats_strip(meeting_count: int) -> str:
    return f"""
    <div style="display:flex; gap:14px; margin-top:18px;">
        <div class="mm-card" style="flex:1; text-align:center; padding:12px;">
            <div class="mm-eyebrow" style="margin-bottom:6px;">meetings processed</div>
            <div class="mm-mono" style="font-size:1.6rem; color:{SIGNAL};">{meeting_count:02d}</div>
        </div>
        <div class="mm-card" style="flex:1; text-align:center; padding:12px;">
            <div class="mm-eyebrow" style="margin-bottom:6px;">pipeline stages</div>
            <div class="mm-mono" style="font-size:1.6rem; color:{DATA};">{len(PIPELINE_STAGES):02d}</div>
        </div>
        <div class="mm-card" style="flex:1; text-align:center; padding:12px;">
            <div class="mm-eyebrow" style="margin-bottom:6px;">max duration</div>
            <div class="mm-mono" style="font-size:1.6rem; color:{PAPER};">15:00</div>
        </div>
    </div>
    """