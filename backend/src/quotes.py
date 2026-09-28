"""#4 Quote Authenticity Detection — semantic match, not literal."""
import re
from sentence_transformers import util
from src.models import get_spacy, get_sbert
from src.retrieve import search

# "X said/once said/famously said '...'", or any quoted span >= 12 chars.
ATTR = re.compile(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\s+(?:once said|said|famously said|stated|wrote)[,:]?\s*[\"“']?(.+)", re.U)
QUOTED = re.compile(r"[\"“”']([^\"“”']{12,})[\"“”']")


def detect_quotes(text):
    """Return list of {quote, attributed_to}."""
    nlp = get_spacy()
    out, seen = [], set()
    doc = nlp(text)
    for sent in doc.sents:
        s = sent.text.strip()
        person = next((e.text for e in sent.ents if e.label_ == "PERSON"), None)
        q = None
        m = QUOTED.search(s)
        if m:
            q = m.group(1).strip()
        else:
            a = ATTR.search(s)
            if a:
                person = person or a.group(1).strip()
                q = a.group(2).strip().strip('"“”\'')
        if q and q.lower() not in seen and len(q) > 12:
            seen.add(q.lower())
            out.append({"quote": q, "attributed_to": person})
    return out


def verify_quote(quote, person):
    """Search the quote, semantically match snippets, check attribution."""
    query = f'"{quote}" {person or ""}'.strip()
    results = search(query, max_results=5)
    if not results:
        return {"quote": quote, "attributed_to": person, "status": "Unverified",
                "confidence": 0.0, "notes": "No matching sources found online.",
                "evidence": []}
    sbert = get_sbert()
    q_emb = sbert.encode(quote, convert_to_tensor=True)
    best_sim, best = 0.0, None
    attr_found = False
    for r in results:
        text = (r["snippet"] or "") + " " + (r["title"] or "")
        sim = float(util.cos_sim(q_emb, sbert.encode(text, convert_to_tensor=True))[0][0])
        if person and person.lower() in text.lower():
            attr_found = True
        if sim > best_sim:
            best_sim, best = sim, r
    if best_sim >= 0.7 and (attr_found or not person):
        status, notes = "Likely Authentic", f"Closely matches wording in credible sources" + (f", attributed to {person}." if person else ".")
    elif best_sim >= 0.7 and person and not attr_found:
        status, notes = "Possibly Misattributed", f"Wording matches online, but attribution to {person} not confirmed in sources."
    elif best_sim >= 0.45:
        status, notes = "Partial Match", "Similar phrasing found, but wording may be altered."
    else:
        status, notes = "Unverified", "No close match found; quote may be fabricated or paraphrased."
    return {"quote": quote, "attributed_to": person, "status": status,
            "confidence": round(best_sim, 2), "notes": notes,
            "evidence": [best] if best else []}


def analyze_quotes(text):
    return [verify_quote(q["quote"], q["attributed_to"]) for q in detect_quotes(text)]
