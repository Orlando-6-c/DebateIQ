"""Step 4 — DuckDuckGo retrieval (free) + source credibility tier (#2)."""
from ddgs import DDGS

HIGH = (".gov", ".gov.pk", "un.org", "unesco.org", "worldbank.org", "imf.org",
        "who.int", "oecd.org", ".edu", "europa.eu", "weforum.org")
MED = ("reuters.com", "bbc.com", "apnews.com", "dawn.com", "nytimes.com",
       "theguardian.com", "aljazeera.com", "nature.com", "sciencedirect.com",
       "wikipedia.org", "britannica.com", "tribune.com.pk")

# Pretty names for grounded reasoning text.
NAMES = {
    "worldbank.org": "the World Bank", "un.org": "the United Nations",
    "unesco.org": "UNESCO", "imf.org": "the IMF", "who.int": "the WHO",
    "weforum.org": "the World Economic Forum", "oecd.org": "the OECD",
    "reuters.com": "Reuters", "bbc.com": "the BBC", "apnews.com": "AP News",
    "dawn.com": "Dawn", "nytimes.com": "the New York Times",
    "theguardian.com": "The Guardian", "aljazeera.com": "Al Jazeera",
    "nature.com": "Nature", "wikipedia.org": "Wikipedia",
    "britannica.com": "Britannica", "tribune.com.pk": "The Express Tribune",
}


def _tier(url):
    u = (url or "").lower()
    if any(d in u for d in HIGH):
        return "High", 1.0
    if any(d in u for d in MED):
        return "Medium", 0.75
    return "Low", 0.4


def _friendly(url):
    u = (url or "").lower()
    for dom, name in NAMES.items():
        if dom in u:
            return name
    # fall back to bare domain
    try:
        host = u.split("//")[-1].split("/")[0].replace("www.", "")
        return host
    except Exception:
        return "a web source"


def search(query, max_results=5):
    out = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, region="pk-en"):
                url = r.get("href") or r.get("url", "")
                tier, weight = _tier(url)
                out.append({"title": r.get("title", ""), "url": url,
                            "snippet": r.get("body", ""), "tier": tier,
                            "credibility": weight, "source": _friendly(url)})
    except Exception as e:
        print(f"[retrieve] search failed: {e}")
    return out
