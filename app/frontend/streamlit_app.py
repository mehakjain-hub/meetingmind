import streamlit as st
import tempfile
from pathlib import Path
import sys

# anchor to project root so 'app.*' imports resolve regardless of cwd or how streamlit was launched
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.pipeline.preprocess import preprocess_audio
from app.pipeline.transcribe import transcribe_audio
from app.pipeline.diarize import diarize
from app.pipeline.align import align
from app.pipeline.merge import merge_transcript_with_speakers
from app.pipeline.clean import clean_turns

st.set_page_config(page_title = "MeetingMind", layout = "wide")
st.title("MeetingMind")

MAX_DURATION_SECONDS = 15*60

uploaded_file = st.file_uploader(
    "Upload a meeting recording",
    type = ["wav", "mp3", "m4a"],
)

if uploaded_file is not None:
    # persist to a temp path since pipeline functions expect a filesystem path, not bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.read())
        raw_audio_path = tmp.name
    st.audio(uploaded_file)
    if st.button("Run Pipeline"):
        with st.spinner("Preprocessing audio..."):
            wav_path = preprocess_audio(raw_audio_path)
        with st.spinner("Transcribing..."):
            whisper_segments, detected_language = transcribe_audio(
                wav_path, model_size = "small", language = "en"
            )
        with st.spinner("Aligning transcript..."):
            aligned_segments = align(wav_path, whisper_segments, language_code = "en")
        with st.spinner("Running speaker diarization..."):
            diarization_segments = diarize(wav_path)
        with st.spinner("Merging transcript + speakers..."):
            turns = merge_transcript_with_speakers(aligned_segments, diarization_segments)
        with st.spinner("Cleaning transcript..."):
            cleaned_turns = clean_turns(turns)
        st.session_state["cleaned_turns"] = cleaned_turns
        st.success("Pipeline Complete!")

if "cleaned_turns" in st.session_state:
    st.subheader("Raw Transcript")
    for turn in st.session_state["cleaned_turns"]:
        st.markdown(f"**{turn['speaker']}** ({turn['start']:.1f}s-{turn['end']:.1f}s: {turn['text']})")