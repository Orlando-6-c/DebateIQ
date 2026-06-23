"""Optional LLM-backed reasoning for claim extraction + evidence verification.

Far more accurate than the local NLI model at deciding support vs. dispute and at
catching claims. Enabled by env vars; if unset, the pipeline falls back to local.

Env:
  LLM_PROVIDER   gemini | openai        (default gemini)
  LLM_API_KEY    your key
  LLM_MODEL      e.g. gemini-1.5-flash  (free) | gpt-4o-mini | llama-3.3-70b-versatile
  LLM_BASE_URL   only for openai-compatible (Groq: https://api.groq.com/openai/v1)
"""
import os, json, re
from urllib.parse import urlparse

PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
API_KEY = os.environ.get("LLM_API_KEY", "").strip()
MODEL = os.environ.get("LLM_MODEL", "").strip() or ("gemini-1.5-flash" if PROVIDER == "gemini" else "gpt-4o-mini")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")

_TWO_PART = {"co.uk", "com.pk", "gov.pk", "org.pk", "edu.pk", "ac.uk", "com.au", "co.in", "org.uk"}


def available():
    return bool(API_KEY)


def _domain(url):
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
        p = host.split(".")
        if len(p) >= 3 and ".".join(p[-2:]) in _TWO_PART:
            return ".".join(p[-3:])
        return ".".join(p[-2:]) if len(p) >= 2 else host
    except Exception:
        return url or "unknown"


def _parse_json(text):
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _chat(prompt):
    """Call the configured LLM, return raw text or None on any failure."""
    if not API_KEY:
        return None
    import requests
    try:
        if PROVIDER == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
            body = {"contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0, "response_mime_type": "application/json"}}
            r = requests.post(url, json=body, timeout=60)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:  # openai-compatible (OpenAI, Groq, OpenRouter, ...)
            r = requests.post(f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"model": MODEL, "temperature": 0,
                      "response_format": {"type": "json_object"},
                      "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[llm] call failed: {e}")
        return None


# ---------- claim extraction ----------
def extract_claims(text):
    prompt = (
        "You are a rigorous fact-checking assistant. From the SPEECH below, extract every "
        "CHECK-WORTHY FACTUAL CLAIM: statements asserting something verifiable (statistics, "
        "historical facts, events, attributions/quotes, named-entity or quantitative claims). "
        "Exclude opinions, greetings, questions and pure rhetoric. For each claim give the claim "
        "text (lightly cleaned) and a concise web-search query to verify it.\n"
        'Return ONLY JSON: {"claims":[{"claim":"...","query":"..."}]}\n\nSPEECH:\n' + text[:6000])
    data = _parse_json(_chat(prompt))
    if not data or "claims" not in data:
        return None
    return [{"claim": c.get("claim", "").strip(), "query": c.get("query", c.get("claim", "")).strip()}
            for c in data["claims"] if c.get("claim")]


# ---------- claim verification ----------
LABELS = ["Verified", "Likely False", "Disputed", "Insufficient Evidence"]


def verify_claims(items):
    """items: [{claim, evidence:[{title,snippet,url,tier}]}] -> aligned verdict dicts or None."""
    payload = []
    for it in items:
        ev = [{"index": i, "title": (e.get("title") or "")[:120],
               "snippet": (e.get("snippet") or "")[:300], "url": e.get("url", "")}
              for i, e in enumerate(it["evidence"])]
        payload.append({"claim": it["claim"], "evidence": ev})

    prompt = (
        "You judge factual claims against retrieved web evidence. For EACH claim:\n"
        "1) For each evidence item decide stance: \"supports\", \"disputes\", or \"irrelevant\" "
        "to the claim (read carefully — do not confuse topical overlap with support).\n"
        "2) Give an overall verdict, STRICTLY one of: Verified, Likely False, Disputed, "
        "Insufficient Evidence.\n"
        "Rules: Verified = multiple independent credible sources support and none credibly dispute. "
        "Likely False = credible sources dispute it. Disputed = credible sources both support and "
        "dispute. Insufficient Evidence = evidence missing, irrelevant, or low-quality. Never guess.\n"
        "3) confidence 0..1 and a one-sentence reasoning.\n"
        'Return ONLY JSON preserving claim order: {"results":[{"verdict":"...","confidence":0.0,'
        '"reasoning":"...","stances":[{"index":0,"stance":"supports"}]}]}\n\nINPUT:\n'
        + json.dumps({"claims": payload})[:12000])
    data = _parse_json(_chat(prompt))
    if not data or "results" not in data or len(data["results"]) != len(items):
        return None
    return data["results"]


def build_claim_result(item, verdict):
    """Pure: assemble a claim dict matching the dashboard shape from LLM verdict."""
    label = verdict.get("verdict", "Insufficient Evidence")
    if label not in LABELS:
        label = "Insufficient Evidence"
    stances = {s.get("index"): s.get("stance") for s in verdict.get("stances", [])}
    supporting, contradicting = [], []
    for i, e in enumerate(item["evidence"]):
        st = stances.get(i)
        if st == "supports":
            supporting.append(e)
        elif st == "disputes":
            contradicting.append(e)
    sup_dom = {_domain(e["url"]) for e in supporting if e.get("tier") in ("High", "Medium")}
    con_dom = {_domain(e["url"]) for e in contradicting if e.get("tier") in ("High", "Medium")}
    indep = sup_dom | con_dom
    return {"claim": item["claim"], "score": 1.0, "method": "llm",
            "label": label, "confidence": round(float(verdict.get("confidence", 0)), 2),
            "note": verdict.get("reasoning", ""),
            "supporting": supporting[:3], "contradicting": contradicting[:3],
            "diversity": {"independent_sources": len(indep), "single_source": len(indep) <= 1,
                          "supporting_sources": len(sup_dom), "contradicting_sources": len(con_dom),
                          "low_credibility_only": False}}


# ---------- quote authenticity ----------
def verify_quotes(items):
    """items: [{quote, person, evidence:[{title,snippet,url}]}] -> aligned dicts or None."""
    payload = [{"quote": it["quote"], "attributed_to": it.get("person") or "unknown",
                "evidence": [{"title": (e.get("title") or "")[:120],
                              "snippet": (e.get("snippet") or "")[:300]} for e in it["evidence"]]}
               for it in items]
    prompt = (
        "Decide whether each quote is authentic and correctly attributed, using the evidence. "
        "status STRICTLY one of: Authentic, Misattributed, Altered, Unverified. "
        "confidence 0..1, one-sentence notes.\n"
        'Return ONLY JSON preserving order: {"results":[{"status":"...","confidence":0.0,"notes":"..."}]}'
        "\n\nINPUT:\n" + json.dumps({"quotes": payload})[:10000])
    data = _parse_json(_chat(prompt))
    if not data or "results" not in data or len(data["results"]) != len(items):
        return None
    return data["results"]
