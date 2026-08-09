import sys
import tempfile
from pathlib import Path
import streamlit as st
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from app.frontend.utils.theme import inject_theme, render_waveform_meter, PIPELINE_STAGES, speaker_chip_html, ensure_session_defaults

inject_theme()
ensure_session_defaults()
MAX_DURATION_SECONDS = 15 * 60

def get_duration_seconds(path: str) -> float:
    with sf.SoundFile(path) as f:
        return len(f) / f.samplerate

def turns_to_text(turns: list[dict]) -> str:
    return "\n".join(f"Speaker {t['speaker']}: {t['text']}" for t in turns)

st.header("Upload a meeting recording")

uploaded_file = st.file_uploader(
    "Upload a meeting recording",
    type=["wav", "mp3", "m4a"],
)

if uploaded_file is not None and st.session_state.pipeline_status == "idle":
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.read())
        raw_audio_path = tmp.name
    duration = get_duration_seconds(raw_audio_path)
    if duration > MAX_DURATION_SECONDS:
        st.error(
            f"This recording is {duration/60:.1f} min long. MeetingMind v1 supports "
            f"recordings up to 15 minutes."
        )
    else:
        st.audio(uploaded_file)
        title = st.text_input("Meeting title", value=Path(uploaded_file.name).stem)
        agenda = st.text_area(
            "Agenda (optional, semicolon-separated)",
            placeholder="Discuss Q3 roadmap; review budget",
        )
        model_size = st.selectbox(
            "Whisper model size", ["small", "medium"], index=None,
            placeholder="Choose model size",
        )
        language_choice = st.radio(
            "Language", ["Force English (en)", "Auto-detect"], index=None,
        )
        ready = model_size is not None and language_choice is not None
        if not ready:
            st.caption("Select a model size and a language mode to enable Run.")
        if st.button("Run Pipeline", type="primary", disabled=not ready):
            st.session_state.raw_audio_path = raw_audio_path
            st.session_state.meeting_title = title
            st.session_state.meeting_agenda = agenda or None
            st.session_state.model_size = model_size
            st.session_state.language = "en" if language_choice == "Force English (en)" else None
            st.session_state.pipeline_status = "running"
            st.rerun()

if st.session_state.pipeline_status == "running":
    raw_audio_path = st.session_state.raw_audio_path
    title = st.session_state.meeting_title
    agenda = st.session_state.meeting_agenda
    model_size = st.session_state.model_size
    language = st.session_state.language
    meter_placeholder = st.empty()
    caption_placeholder = st.empty()
    caption_placeholder.caption("Loading models...")

    from app.pipeline.preprocess import preprocess_audio
    from app.pipeline.transcribe import transcribe_audio
    from app.pipeline.diarize import diarize
    from app.pipeline.align import align
    from app.pipeline.merge import merge_transcript_with_speakers
    from app.pipeline.clean import clean_turns
    from app.pipeline.extract import extract_meeting_summary
    from app.db.crud import create_meeting, save_transcript, save_summary, save_action_items
    from app.db.session import session_scope

    def show_stage(i: int, errored: bool = False):
        meter_placeholder.markdown(render_waveform_meter(i, errored=errored), unsafe_allow_html=True)
        if i < len(PIPELINE_STAGES):
            caption_placeholder.caption(f"Running: {PIPELINE_STAGES[i]}...")
        else:
            caption_placeholder.caption("Done.")
    try:
        show_stage(0)
        wav_path = preprocess_audio(raw_audio_path)
        show_stage(1)
        whisper_segments, detected_language = transcribe_audio(
            wav_path, model_size=model_size, language=language
        )
        show_stage(2)
        aligned_segments = align(wav_path, whisper_segments, language_code=detected_language)
        show_stage(3)
        diarization_segments = diarize(wav_path)
        show_stage(4)
        turns = merge_transcript_with_speakers(aligned_segments, diarization_segments)
        show_stage(5)
        cleaned_turns = clean_turns(turns)
        raw_text = turns_to_text(turns)
        cleaned_text = turns_to_text(cleaned_turns)
        duration_seconds = max((t["end"] for t in turns), default=0.0)
        show_stage(6)
        agenda_items = (
            [item.strip() for item in agenda.split(";") if item.strip()]
            if agenda else None
        )
        result = extract_meeting_summary(cleaned_text, agenda_items=agenda_items)
        show_stage(7)
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
        show_stage(len(PIPELINE_STAGES))  # all bars done
        st.session_state.meeting_id = meeting_id
        st.session_state.pop("results_data", None)  # clear stale results from a previous meeting
        st.session_state.raw_turns = turns
        st.session_state.cleaned_turns = cleaned_turns
        st.session_state.pipeline_status = "done"
        st.rerun()
    except Exception as e:
        st.session_state.pipeline_status = "error"
        st.session_state.error_message = str(e)
        st.rerun()

if st.session_state.pipeline_status == "error":
    st.error(f"Pipeline failed: {st.session_state.error_message}")
    if st.button("Try again"):
        st.session_state.pipeline_status = "idle"
        st.session_state.error_message = None
        st.rerun()

if st.session_state.pipeline_status == "done":
    st.success(f"Pipeline Complete! meeting_id = {st.session_state.meeting_id}")
    st.subheader("Cleaned Transcript")
    for turn in st.session_state.cleaned_turns:
        chip = speaker_chip_html(turn["speaker"])
        st.markdown(
            f'{chip}<span class="mm-mono" style="color:#8B92A0; font-size:0.8rem;">'
            f'{turn["start"]:.1f}s–{turn["end"]:.1f}s</span><br>{turn["text"]}',
            unsafe_allow_html=True,
        )
    st.info("Head to the **Results** page for summary, decisions, and action items.")
    if st.button("Process another recording"):
        st.session_state.pipeline_status = "idle"
        st.session_state.meeting_id = None
        st.rerun()