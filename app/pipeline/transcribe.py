from faster_whisper import WhisperModel
from onnxruntime.transformers.benchmark_helper import inference_ort_with_io_binding


def transcribe_audio(audio_path: str, model_size: str = "small"):
    """
    Transcribe an audio file using faster-whisper (int8 quantized).
    Returns a list of segments with start/end timestamps and text.
    """
    model = WhisperModel(model_size, device = 'cpu', compute_type = 'int8')
    segments, info = model.transcribe(audio_path, beam_size = 5, word_timestamps = True)
    print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")
    results = []
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        results.append({"start" : segment.start, "end" : segment.end, "text" : segment.text})

    return results

if __name__ == "__main__":
    transcribe_audio("sample_data/meeting-clip2_16k.wav")