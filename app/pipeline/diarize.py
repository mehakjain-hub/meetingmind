import argparse
import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

load_dotenv()

def diarize(audio_path: str):
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not found in .env")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )

    with ProgressHook() as hook:
        diarization = pipeline(audio_path, hook=hook)

    segments = []
    for turn, _, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 2),
            "end": round(turn.end, 2),
            "speaker": speaker
        })
        print(f"[{turn.start:.2f}s - {turn.end:.2f}s] {speaker}")

    return segments

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run pyannote speaker diarization on an audio file")
    parser.add_argument("audio_file", help="Path to the audio file (16kHz mono WAV recommended)")
    args = parser.parse_args()

    diarize(args.audio_file)