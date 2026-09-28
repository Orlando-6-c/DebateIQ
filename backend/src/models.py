"""Shared, lazily-cached model loaders (so each model loads once)."""
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_spacy = _sbert = _nli = _nli_tok = None


def get_spacy():
    global _spacy
    if _spacy is None:
        import spacy
        try:
            _spacy = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            _spacy = spacy.load("en_core_web_sm")
    return _spacy


def get_sbert():
    global _sbert
    if _sbert is None:
        from sentence_transformers import SentenceTransformer
        _sbert = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
    return _sbert


def get_nli():
    global _nli, _nli_tok
    if _nli is None:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
        _nli_tok = AutoTokenizer.from_pretrained(name)
        _nli = AutoModelForSequenceClassification.from_pretrained(name).to(DEVICE).eval()
    return _nli_tok, _nli, DEVICE


# Optional trained claim-detector. Set env CLAIM_MODEL to a HF repo id or local
# path to enable it; otherwise the app uses the hand-coded heuristic.
import os
_claim = None
_claim_loaded = False

def get_claim_clf():
    """Return (tokenizer, model, checkworthy_index) or None if not configured."""
    global _claim, _claim_loaded
    if _claim_loaded:
        return _claim
    _claim_loaded = True
    repo = os.environ.get("CLAIM_MODEL", "").strip()
    if not repo:
        return None
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        tok = AutoTokenizer.from_pretrained(repo)
        model = AutoModelForSequenceClassification.from_pretrained(repo).to(DEVICE).eval()
        id2label = {int(k): str(v).lower() for k, v in model.config.id2label.items()}
        idx = next((i for i, l in id2label.items() if "check" in l or l in ("1", "cfs")), 1)
        _claim = (tok, model, idx)
        print(f"[claim-clf] loaded trained detector: {repo}")
    except Exception as e:
        print(f"[claim-clf] load failed, using heuristic: {e}")
        _claim = None
    return _claim
