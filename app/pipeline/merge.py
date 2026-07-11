import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from transcribe import transcribe_audio
from align import align
from diarize import diarize


def assign_speaker(word_start, word_end, diarization_segments):
    best_overlap = 0
    best_speaker = None
    for seg in diarization_segments:
        overlap = min(word_end, seg["end"]) - max(word_start, seg["start"])
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = seg["speaker"]
    return best_speaker


def merge_transcript_with_speakers(aligned_segments, diarization_segments):
    tagged_words = []
    for segment in aligned_segments:
        for word in segment.get("words", []):
            if "start" not in word or "end" not in word:
                continue
            speaker = assign_speaker(float(word["start"]), float(word["end"]), diarization_segments)
            tagged_words.append({
                "word": word["word"],
                "start": float(word["start"]),
                "end": float(word["end"]),
                "speaker": speaker
            })

    turns = []
    current_turn = None
    for w in tagged_words:
        if current_turn is None or w["speaker"] != current_turn["speaker"]:
            if current_turn:
                turns.append(current_turn)
            current_turn = {
                "speaker": w["speaker"],
                "start": w["start"],
                "end": w["end"],
                "text": w["word"].strip()
            }
        else:
            current_turn["end"] = w["end"]
            current_turn["text"] += " " + w["word"].strip()
    if current_turn:
        turns.append(current_turn)

    return turns


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge aligned transcript with speaker diarization")
    parser.add_argument("audio_path")
    parser.add_argument("--model_size", default="small")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    whisper_segments, detected_language = transcribe_audio(args.audio_path, args.model_size)
    aligned_segments = align(args.audio_path, whisper_segments, args.language)
    diarization_segments = diarize(args.audio_path)

    turns = merge_transcript_with_speakers(aligned_segments, diarization_segments)

    for turn in turns:
        print(f"[{turn['start']:.2f}s -> {turn['end']:.2f}s] Speaker {turn['speaker']}: {turn['text']}")