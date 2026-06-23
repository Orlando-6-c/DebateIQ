"""Orchestrator. Uses LLM reasoning for claims/quotes when configured (accurate),
otherwise falls back to the local heuristic + NLI pipeline."""
from src.transcribe import transcribe
from src.extract import extract_claims
from src.retrieve import search
from src.verify import verify
from src.quotes import analyze_quotes, detect_quotes
from src.analyze import manipulation_risk, detect_fallacies, speech_metrics, pakistani_context
from src.judge import judge_summary
from src.translate import maybe_translate
from src.auth import DEFAULT_SETTINGS
from src import llm

LANG_LABEL = {"ur": "Urdu", "roman-ur": "Roman Urdu", "en": "English"}


def _llm_claims(analyzed, max_claims):
    """Return (results, True) on success, or (None, False) to signal fallback."""
    extracted = llm.extract_claims(analyzed)
    if extracted is None:
        return None, False
    items = [{"claim": c["claim"], "evidence": search(c["query"], 6)} for c in extracted[:max_claims]]
    if not items:
        return [], True
    verdicts = llm.verify_claims(items)
    if verdicts is None:
        return None, False
    return [llm.build_claim_result(items[i], verdicts[i]) for i in range(len(items))], True


def _llm_quotes(analyzed):
    detected = detect_quotes(analyzed)
    if not detected:
        return []
    items = [{"quote": q["quote"], "person": q["attributed_to"],
              "evidence": search(f'"{q["quote"]}" {q["attributed_to"] or ""}', 5)} for q in detected]
    res = llm.verify_quotes(items)
    if res is None:
        return analyze_quotes(analyzed)  # fallback to local quote check
    return [{"quote": detected[i]["quote"], "attributed_to": detected[i]["attributed_to"],
             "status": res[i].get("status", "Unverified"),
             "confidence": round(float(res[i].get("confidence", 0)), 2),
             "notes": res[i].get("notes", ""), "evidence": items[i]["evidence"][:1]}
            for i in range(len(detected))]


def analyze(text="", audio_path="", threshold=0.4, max_claims=8, duration=0.0, weights=None):
    weights = weights or DEFAULT_SETTINGS
    original = text.strip()
    if not original and audio_path:
        original, duration = transcribe(audio_path)

    analyzed, translated, lang = maybe_translate(original)

    engine = "local"
    results = None
    if llm.available():
        results, ok = _llm_claims(analyzed, max_claims)
        if ok and results is not None:
            engine = "llm"
            quotes = _llm_quotes(analyzed)
        else:
            results = None  # fall through to local

    if results is None:  # local fallback (unchanged behaviour)
        claims = extract_claims(analyzed, threshold=threshold)[:max_claims]
        results = [{**c, **verify(c["claim"], search(c["query"], 5))} for c in claims]
        quotes = analyze_quotes(analyzed)

    manip = manipulation_risk(analyzed)
    fallacies = detect_fallacies(analyzed)
    metrics = speech_metrics(original, duration)
    pak = pakistani_context(original)
    judge = judge_summary(results, manip, fallacies, metrics, pak, quotes, weights)

    return {"transcript": original,
            "translation": {"translated": translated, "language": lang,
                            "language_label": LANG_LABEL.get(lang, lang)},
            "engine": engine, "claims": results, "quotes": quotes,
            "manipulation": manip, "fallacies": fallacies, "metrics": metrics,
            "pakistani": pak, "judge": judge}
