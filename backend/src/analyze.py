"""#3 Manipulation risk · #6 Fallacy detection · #7 Speech metrics · #8 Pakistani context."""
import re

# ---- #3 Manipulation risk ----
VAGUE = ["some reports", "according to some", "many believe", "people say",
         "studies say", "experts say", "it is said", "some say", "sources say"]
FEAR = ["catastrophe", "disaster", "destroy", "collapse", "crisis", "threat",
        "danger", "doom", "devastat", "chaos", "ruin"]
ABSOLUTES = ["everyone knows", "obviously", "without a doubt", "undeniable",
             "clearly", "100%", "always", "never", "no one can deny", "certainly"]
INTENSIFIERS = ["extremely", "massively", "completely", "totally", "utterly", "incredibly"]


def manipulation_risk(text):
    t = text.lower()
    reasons, score = [], 0
    if any(p in t for p in VAGUE):
        reasons.append("Vague attribution (e.g. 'some reports') without naming a specific source."); score += 2
    if sum(f in t for f in FEAR) >= 2:
        reasons.append("Fear-based or alarmist language used."); score += 1
    if any(a in t for a in ABSOLUTES):
        reasons.append("Unsupported certainty / absolute claims."); score += 1
    if sum(i in t for i in INTENSIFIERS) >= 2:
        reasons.append("Heavy use of emotional intensifiers."); score += 1
    level = "High" if score >= 3 else "Medium" if score >= 1 else "Low"
    return {"level": level, "reasons": reasons or ["No strong manipulation signals detected."]}


# ---- #6 Fallacy detection ----
FALLACY_PATTERNS = [
    ("False Dilemma", [r"either .* or ", r"not mutually exclusive", r"only two (?:options|choices)", r"if not .* then"],
     "Presents two options as the only possibilities when others may exist."),
    ("Slippery Slope", [r"will lead to", r"before you know it", r"inevitably", r"next thing you know"],
     "Assumes one step necessarily triggers a chain of negative outcomes."),
    ("Hasty Generalization", [r"\ball (?:of them|people|countries)\b", r"every single", r"always the case"],
     "Draws a broad conclusion from limited examples."),
    ("Appeal to Fear", [r"if we don.t .* then", r"we will all", r"face (?:disaster|collapse|ruin)"],
     "Uses fear of consequences instead of evidence to persuade."),
]


def detect_fallacies(text):
    t = text.lower()
    found = []
    for name, pats, expl in FALLACY_PATTERNS:
        if any(re.search(p, t) for p in pats):
            found.append({"fallacy": name, "explanation": expl})
    return found


# ---- #7 Speech intelligence metrics ----
FILLERS = ["um", "uh", "er", "like", "you know", "basically", "actually", "literally", "i mean"]
HEDGES = ["maybe", "perhaps", "might", "possibly", "i think", "probably", "sort of", "kind of"]
CONNECTIVES = ["because", "therefore", "however", "although", "thus", "since", "evidence", "consequently", "moreover"]


def speech_metrics(text, duration_sec=0.0):
    words = re.findall(r"\b\w+\b", text.lower())
    n = max(1, len(words))
    sents = max(1, len(re.findall(r"[.!?]+", text)))
    fillers = sum(text.lower().count(f) for f in FILLERS)
    hedges = sum(text.lower().count(h) for h in HEDGES)
    connect = sum(text.lower().count(c) for c in CONNECTIVES)
    wpm = round(len(words) / (duration_sec / 60), 0) if duration_sec > 5 else None
    filler_rate = round(fillers / n * 100, 1)
    hedge_rate = round(hedges / n * 100, 1)
    arg_density = round(connect / sents, 2)
    confidence = "High" if hedge_rate < 1 else "Moderate" if hedge_rate < 3 else "Low"
    return {"words": len(words), "wpm": wpm, "filler_pct": filler_rate,
            "argument_density": arg_density, "confidence_level": confidence,
            "filler_usage": "Low" if filler_rate < 2 else "Moderate" if filler_rate < 5 else "High"}


# ---- #8 Pakistani context intelligence ----
ROMAN_URDU = {"hai", "nahi", "kya", "aap", "hum", "magar", "lekin", "kyunki",
              "bohat", "bahut", "acha", "theek", "yeh", "woh", "kuch", "sab",
              "humein", "hamara", "inshallah", "mashallah", "bilkul", "zaroor"}
MUN = ["the delegate of", "honourable chair", "this house", "point of order",
       "fellow delegates", "the floor", "draft resolution", "respected chair"]
SUSPECT_STAT = re.compile(r"(un|unesco|world bank|imf|who)\b.{0,40}\b\d{1,3}\s?%", re.I)


def pakistani_context(text):
    t = text.lower()
    toks = set(re.findall(r"\b\w+\b", t))
    urdu = sorted(toks & ROMAN_URDU)
    flags = []
    if urdu:
        flags.append(f"Urdu–English code-switching detected ({', '.join(urdu[:6])}).")
    if any(m in t for m in MUN):
        flags.append("MUN/diplomatic register detected — formal debate context.")
    if SUSPECT_STAT.search(text):
        flags.append("Big-organisation statistic detected — commonly fabricated in debates; verify carefully.")
    return {"code_switching": bool(urdu), "urdu_terms": urdu,
            "flags": flags or ["No Pakistan-specific signals detected."]}


# ---- Speaker name auto-detection (Judge Mode) ----
import re as _re
_INTRO_CUE = _re.compile(
    r"(?:my name is|i am|i'm|this is|myself|name is|i'm called|call me)\s+"
    r"([A-Za-z][A-Za-z'.-]+(?:\s+[A-Za-z][A-Za-z'.-]+){0,2})", _re.IGNORECASE)
_NOT_NAME = {"a", "an", "the", "very", "really", "here", "from", "going", "student",
             "delegate", "speaker", "representing", "pleased", "honoured", "honored",
             "glad", "happy", "grateful", "standing", "speaking", "proud", "today",
             "your", "my", "his", "her", "their", "about", "not", "so"}


_STOP_TOKENS = _NOT_NAME | {"and", "i", "is", "was", "will", "who", "that", "am",
                            "but", "or", "of", "for", "with", "to"}


def _extract_name(cand):
    """Keep only the leading run of name-like tokens (stops at connectors/stopwords)."""
    out = []
    for tok in cand.split():
        t = tok.strip(",.")
        if t.isalpha() and t.lower() not in _STOP_TOKENS:
            out.append(t)
        else:
            break
    if 1 <= len(out) <= 3:
        return " ".join(w.capitalize() for w in out)
    return None


def detect_speaker_name(text):
    """Find a self-introduced name in the opening of a speech. Returns name or None."""
    head = (text or "").strip()[:400]
    if not head:
        return None
    m = _INTRO_CUE.search(head)
    if m:
        name = _extract_name(m.group(1))
        if name:
            return name
    try:  # fall back to first PERSON entity in the intro region
        from src.models import get_spacy
        for e in get_spacy()(head).ents:
            if e.label_ == "PERSON":
                name = _extract_name(e.text)
                if name:
                    return name
    except Exception:
        pass
    return None
