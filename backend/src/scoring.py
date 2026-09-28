"""Customizable scoring engine. Three sub-scores (Factual, Integrity, Delivery)
blended by user weights into a 0-10 score."""

VERDICT_PTS = {"Verified": 10, "Partially Supported": 7, "Disputed": 5,
               "Insufficient Evidence": 5, "Partially Disputed": 3, "Likely False": 0}


def factual_subscore(claims):
    if not claims:
        return 5.0
    pts = [VERDICT_PTS.get(c["label"], 5) for c in claims]
    return round(sum(pts) / len(pts), 1)


def integrity_subscore(manipulation, fallacies, quotes, sensitivity=1.0):
    score = 10.0
    score -= {"Low": 0, "Medium": 2, "High": 4}[manipulation["level"]] * sensitivity
    score -= min(5, 1.5 * len(fallacies))
    bad = sum(1 for q in quotes if q["status"] not in ("Likely Authentic", "Partial Match"))
    score -= min(3, 1.5 * bad)
    return round(max(0.0, min(10.0, score)), 1)


def delivery_subscore(metrics):
    base = {"High": 10, "Moderate": 7, "Low": 4}[metrics["confidence_level"]]
    base -= {"Low": 0, "Moderate": 1, "High": 2}[metrics["filler_usage"]]
    base += min(2, metrics["argument_density"] * 2)
    return round(max(0.0, min(10.0, base)), 1)


def compute(claims, manipulation, fallacies, quotes, metrics, weights):
    f = factual_subscore(claims)
    i = integrity_subscore(manipulation, fallacies, quotes, weights.get("manip_sensitivity", 1.0))
    d = delivery_subscore(metrics)
    wf, wi, wd = weights["w_factual"], weights["w_integrity"], weights["w_delivery"]
    total = max(1, wf + wi + wd)
    final = round((f * wf + i * wi + d * wd) / total, 1)
    return {"final": final, "factual": f, "integrity": i, "delivery": d,
            "weights": {"factual": wf, "integrity": wi, "delivery": wd}}
