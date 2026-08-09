import argparse
import whisperx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from transcribe import transcribe_audio

def load_align_model(language_code: str, device: str = "cpu"):
    model_a, metadata = whisperx.load_align_model(language_code = language_code, device = device)
    return model_a, metadata

def align(audio_path: str, segments: list, language_code: str = "en", device: str = "cpu"):
    audio = whisperx.load_audio(audio_path)
    model_a, metadata = load_align_model(language_code, device)
    result = whisperx.align(segments, model_a, metadata, audio, device, return_char_alignments = False)
    return result["segments"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Align Whisper transcript timestamps using whisperX")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--language", default="en")
    parser.add_argument("--model_size", default="small")
    args = parser.parse_args()
    whisper_segments, detected_language = transcribe_audio(args.audio_path, args.model_size)
    aligned_segments = align(args.audio_path, whisper_segments, args.language)

    for seg in aligned_segments:
        print(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['text']}")