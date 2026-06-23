"""Verification engine with anti-bias safeguards.

Principles:
- A directional verdict (Verified / Likely False) requires >=2 INDEPENDENT credible
  sources agreeing. One source is never enough.
- When credible sources both support and contradict, we return DISPUTED and show
  both sides — we do not pick a winner.
- When no credible sources are found, we return INSUFFICIENT EVIDENCE rather than
  guessing.
- Supporting and contradicting evidence are always returned separately.
"""
import torch
from urllib.parse import urlparse
from sentence_transformers import util
from src.models import get_sbert, get_nli

TWO_PART_TLDS = {"co.uk", "com.pk", "gov.pk", "org.pk", "edu.pk", "ac.uk",
                 "com.au", "co.in", "org.uk"}
CREDIBLE = ("High", "Medium")


def registrable_domain(url):
    """Reduce a URL to its independent owner domain (3 pages of one site = 1 source)."""
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
        parts = host.split(".")
        if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_PART_TLDS:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:]) if len(parts) >= 2 else host
    except Exception:
        return url or "unknown"


def _nli_probs(premise, hypothesis):
    tok, nli, device = get_nli()
    inputs = tok(premise, hypothesis, return_tensors="pt",
                 truncation=True, max_length=512).to(device)
    with torch.no_grad():
        logits = nli(**inputs).logits[0]
    probs = torch.softmax(logits, dim=-1).cpu().tolist()
    id2label = {int(k): v.lower() for k, v in nli.config.id2label.items()}
    return {id2label[i]: probs[i] for i in range(len(probs))}


def decide(enriched):
    """Pure decision logic — testable without any model."""
    supporting = [e for e in enriched if e["entail"] > 0.5]
    contradicting = [e for e in enriched if e["contradict"] > 0.5]

    cred_sup = {e["domain"]: e["entail"] for e in supporting if e["tier"] in CREDIBLE}
    cred_con = {e["domain"]: e["contradict"] for e in contradicting if e["tier"] in CREDIBLE}
    nS, nC = len(cred_sup), len(cred_con)
    meanS = sum(cred_sup.values()) / nS if nS else 0.0
    meanC = sum(cred_con.values()) / nC if nC else 0.0

    if nS >= 2 and nC == 0:
        label = "Verified"; conf = min(0.97, meanS * (0.7 + 0.1 * min(3, nS)))
        note = f"{nS} independent credible sources support this; none contradict it."
    elif nC >= 2 and nS == 0:
        label = "Likely False"; conf = min(0.97, meanC * (0.7 + 0.1 * min(3, nC)))
        note = f"{nC} independent credible sources contradict this; none support it."
    elif nS >= 1 and nC >= 1:
        label = "Disputed"; conf = min(0.6, max(meanS, meanC))
        note = "Credible sources disagree — verdict withheld; see both sides below."
    elif nS == 1 and nC == 0:
        label = "Partially Supported"; conf = round(meanS * 0.6, 2)
        note = "Only one credible source supports this — treat as preliminary, not confirmed."
    elif nC == 1 and nS == 0:
        label = "Partially Disputed"; conf = round(meanC * 0.6, 2)
        note = "Only one credible source disputes this — not enough to call it false."
    else:
        label = "Insufficient Evidence"; conf = 0.0
        low_only = any(e["tier"] == "Low" for e in enriched)
        note = ("Only low-credibility sources were found — not enough to verify."
                if low_only else "No relevant credible evidence was retrieved.")

    indep = set(cred_sup) | set(cred_con)
    diversity = {"independent_sources": len(indep), "single_source": len(indep) <= 1,
                 "supporting_sources": nS, "contradicting_sources": nC,
                 "low_credibility_only": label == "Insufficient Evidence" and any(e["tier"] == "Low" for e in enriched)}

    def top(items, key):
        return sorted(items, key=lambda x: x[key], reverse=True)[:3]

    return {"label": label, "confidence": round(conf, 2), "note": note,
            "supporting": top(supporting, "entail"),
            "contradicting": top(contradicting, "contradict"), "diversity": diversity}


def verify(claim, evidence):
    if not evidence:
        return {"label": "Insufficient Evidence", "confidence": 0.0,
                "note": "No web evidence retrieved.", "supporting": [], "contradicting": [],
                "diversity": {"independent_sources": 0, "single_source": True,
                              "supporting_sources": 0, "contradicting_sources": 0,
                              "low_credibility_only": False}}
    sbert = get_sbert()
    claim_emb = sbert.encode(claim, convert_to_tensor=True)
    enriched = []
    for ev in evidence:
        text = ev["snippet"] or ev["title"]
        if not text:
            continue
        rel = float(util.cos_sim(claim_emb, sbert.encode(text, convert_to_tensor=True))[0][0])
        probs = _nli_probs(text, claim)
        enriched.append({**ev, "relevance": round(rel, 2),
                         "entail": round(probs.get("entailment", 0), 2),
                         "contradict": round(probs.get("contradiction", 0), 2),
                         "domain": registrable_domain(ev["url"])})
    return decide(enriched)
