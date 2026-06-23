"""Steps 2 & 3 — sentence split, check-worthiness scoring, NER, query building.
Uses a trained claim-detector if CLAIM_MODEL is set, else the hand-coded heuristic.
"""
import re
from src.models import get_spacy, get_claim_clf

CUE_PHRASES = [
    "according to", "studies show", "research indicates", "reported that",
    "as stated by", "data shows", "statistics show", "the un", "world bank",
    "unesco", "survey", "officially", "confirmed that", "found that",
    "as said by", "once said", "famously said", "quoted", "claims that",
]
QUOTE_PATTERN = re.compile(r"[\"“”'].{8,}[\"“”']")
NUMBER_PATTERN = re.compile(r"\b\d+(\.\d+)?\s?%|\b\d{2,}\b|\bpercent\b", re.I)
FACTUAL_ENTS = {"PERSON", "ORG", "GPE", "NORP", "EVENT", "LAW", "DATE",
                "PERCENT", "MONEY", "CARDINAL", "QUANTITY"}


def _checkworthiness(sent_text, ents):
    text = sent_text.lower()
    score = 0.0
    if any(c in text for c in CUE_PHRASES):
        score += 0.45
    if QUOTE_PATTERN.search(sent_text):
        score += 0.35
    if NUMBER_PATTERN.search(sent_text):
        score += 0.30
    factual = [e for e in ents if e.label_ in FACTUAL_ENTS]
    if factual:
        score += min(0.30, 0.12 * len(factual))
    return min(score, 1.0)


def _build_query(sent_text, ents):
    nlp = get_spacy()
    ent_terms = [e.text for e in ents if e.label_ in FACTUAL_ENTS]
    doc = nlp(sent_text)
    content = [t.text for t in doc if not t.is_stop and not t.is_punct
               and t.pos_ in {"NOUN", "PROPN", "VERB", "NUM"}]
    seen, terms = set(), []
    for term in ent_terms + content:
        k = term.lower()
        if k not in seen:
            seen.add(k); terms.append(term)
    return " ".join(terms[:8]) or sent_text


def _model_scores(texts, clf):
    """Return P(check-worthy) per sentence using the trained detector."""
    import torch
    tok, model, idx = clf
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 16):
            batch = texts[i:i + 16]
            enc = tok(batch, return_tensors="pt", truncation=True, padding=True, max_length=128).to(model.device)
            probs = torch.softmax(model(**enc).logits, dim=-1)[:, idx].cpu().tolist()
            out += probs
    return out


def extract_claims(text, threshold=0.4):
    if not text.strip():
        return []
    doc = get_spacy()(text)
    sents = [s for s in doc.sents if len(s.text.strip()) >= 12]
    clf = get_claim_clf()
    model_scores = _model_scores([s.text.strip() for s in sents], clf) if clf else None
    claims = []
    for i, sent in enumerate(sents):
        s = sent.text.strip()
        ents = list(sent.ents)
        score = model_scores[i] if model_scores is not None else _checkworthiness(s, ents)
        if score >= threshold:
            claims.append({"claim": s, "score": round(float(score), 2),
                           "method": "model" if model_scores is not None else "heuristic",
                           "entities": [(e.text, e.label_) for e in ents],
                           "query": _build_query(s, ents)})
    return claims
