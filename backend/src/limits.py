"""Tier-aware limit helpers (caps passed in by the caller from the tier config)."""
import os, tempfile

FREE_WORD_CAP = 300   # kept for /limits default display
FREE_AUDIO_SEC = 60


def enforce_text(text, cap=FREE_WORD_CAP):
    words = text.split()
    if len(words) <= cap:
        return text, len(words), False
    return " ".join(words[:cap]), len(words), True


def audio_duration(path):
    try:
        import soundfile as sf
        return float(sf.info(path).duration)
    except Exception:
        try:
            import wave
            with wave.open(path) as w:
                return w.getnframes() / float(w.getframerate())
        except Exception:
            return None


def enforce_audio(path, cap=FREE_AUDIO_SEC):
    dur = audio_duration(path)
    if dur is None or dur <= cap:
        return path, dur, False
    try:
        import soundfile as sf
        data, sr = sf.read(path)
        clip = data[: int(cap * sr)]
        tmp = os.path.join(tempfile.gettempdir(), "debateiq_clip.wav")
        sf.write(tmp, clip, sr)
        return tmp, dur, True
    except Exception:
        return path, dur, True
