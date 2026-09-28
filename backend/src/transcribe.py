"""Step 1 — Speech to text using faster-whisper. Returns text + duration (for WPM)."""
from faster_whisper import WhisperModel
import torch

_model = None

def _get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        _model = WhisperModel("base", device=device, compute_type=compute)
    return _model


def transcribe(audio_path: str):
    """Return (transcript_text, duration_seconds)."""
    if not audio_path:
        return "", 0.0
    model = _get_model()
    segments, info = model.transcribe(audio_path, beam_size=5, vad_filter=True)
    segs = list(segments)
    text = " ".join(s.text.strip() for s in segs).strip()
    duration = segs[-1].end if segs else getattr(info, "duration", 0.0)
    return text, float(duration or 0.0)
