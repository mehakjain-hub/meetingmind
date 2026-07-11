import argparse
import os
import soundfile as sf
import torch
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

from app.db.session import ENV_PATH

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def diarize(audio_path: str):
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not found in .env")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )

    data, sample_rate = sf.read(audio_path, dtype="float32")
    if data.ndim == 1:
        data = data[np.newaxis, :]
    else:
        data = data.T
    waveform = torch.from_numpy(data)
    audio_input = {"waveform": waveform, "sample_rate": sample_rate}

    with ProgressHook() as hook:
        diarization = pipeline(audio_input, hook=hook)

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
