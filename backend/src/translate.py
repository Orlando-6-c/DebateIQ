"""Translate-then-analyze bridge. Detects Urdu (script or Roman-Urdu) and
translates to English via deep-translator (free, no API key) so the English
pipeline can analyze it. Falls back to the original text if translation fails.
"""
import re
from src.analyze import ROMAN_URDU

URDU_SCRIPT = re.compile(r"[\u0600-\u06FF]")


def detect_language(text):
    if not text or not text.strip():
        return "en"
    if URDU_SCRIPT.search(text):
        return "ur"
    toks = re.findall(r"\b\w+\b", text.lower())
    if toks and sum(t in ROMAN_URDU for t in toks) / len(toks) >= 0.12:
        return "roman-ur"
    return "en"


def _chunks(s, n=4500):
    return [s[i:i + n] for i in range(0, len(s), n)]


def maybe_translate(text):
    """Return (text_for_analysis, was_translated, detected_lang)."""
    lang = detect_language(text)
    if lang == "en" or not text.strip():
        return text, False, lang
    try:
        from deep_translator import GoogleTranslator
        tr = GoogleTranslator(source="auto", target="en")
        out = " ".join(tr.translate(c) for c in _chunks(text) if c.strip())
        if out and out.strip():
            return out, True, lang
    except Exception as e:
        print(f"[translate] failed, using original: {e}")
    return text, False, lang
