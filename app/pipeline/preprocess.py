# Converts raw meeting audio (any format FFmpeg supports) into 16kHz mono WAV - the format Whisper expects for transcription.

import subprocess
import shutil
from pathlib import Path
from typing import Optional

class PreprocessError(Exception): # Raised when audio preprocessing fails.
    pass

def check_ffmpeg_installed() -> None: # Fail fast with a clear error if FFmpeg isn't on PATH.
    if shutil.which('ffmpeg') is None:
        raise PreprocessError("FFmpeg not found on PATH. Install it and verify with 'ffmpeg -version'.")

def preprocess_audio(input_path: str, output_path: Optional[str] = None) -> str: # Convert an input audio file to 16kHz mono WAV.
    """
    Args:
        input_path: path to the raw uploaded audio file (any format).
        output_path: optional destination path. Defaults to <input_stem>_16k_mono.wav in the same folder.
    Returns:
        The path to the converted WAV file.
    """
    check_ffmpeg_installed()

    in_path = Path(input_path)

    if not in_path.exists():
        raise PreprocessError(f'Input file not found: {input_path}')

    if output_path is None:
        output_path = str(in_path.with_name(f"{in_path.stem}_16k_mono.wav"))

    cmd = ["ffmpeg", "-i", str(in_path), "-ar", "16000", "-ac", "1", "-y", output_path,]
    result = subprocess.run(cmd, capture_output = True, text = True)

    if result.returncode != 0:
        raise PreprocessError(f"FFmpeg failed:\n{result.stderr}")

    return output_path

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description = "Preprocess audio for MeetingMind pipeline.")
    parser.add_argument("input", help = "Path to raw audio file")
    parser.add_argument("-o", "--output", help = "Optional output path", default = None)
    args = parser.parse_args()

    out = preprocess_audio(args.input, args.output)
    print(f"Preprocessed audio written to: {out}")