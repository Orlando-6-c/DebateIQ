"""Speaker score (customizable) + AI judge summary, with anti-bias buckets."""
from src import scoring

BUCKETS = {"Verified": "supported", "Partially Supported": "supported",
           "Disputed": "disputed", "Partially Disputed": "disputed",
           "Likely False": "false", "Insufficient Evidence": "insufficient"}


def judge_summary(results, manipulation, fallacies, metrics, pak, quotes, weights):
    sc = scoring.compute(results, manipulation, fallacies, quotes, metrics, weights)
    counts = {"supported": 0, "disputed": 0, "false": 0, "insufficient": 0}
    for r in results:
        counts[BUCKETS.get(r["label"], "insufficient")] += 1
    indep = [r["diversity"]["independent_sources"] for r in results] or [0]
    avg_sources = round(sum(indep) / len(indep), 1)

    parts = [f"Of {len(results)} verifiable claim(s): {counts['supported']} supported, "
             f"{counts['disputed']} disputed, {counts['false']} likely false, "
             f"{counts['insufficient']} unverifiable on available evidence."]
    if counts["false"] or counts["disputed"]:
        parts.append("Some claims were contradicted or contested by credible sources.")
    elif counts["supported"] and not counts["insufficient"]:
        parts.append("Claims held up against multiple independent sources.")
    parts.append(f"Average independent sources per claim: {avg_sources}.")
    parts.append(f"Delivery showed {metrics['confidence_level'].lower()} confidence "
                 f"with {metrics['filler_usage'].lower()} filler usage.")
    if manipulation["level"] != "Low":
        parts.append(f"{manipulation['level']} manipulation risk flagged.")
    if fallacies:
        parts.append(f"Possible fallac{'y' if len(fallacies)==1 else 'ies'}: "
                     f"{', '.join(f['fallacy'] for f in fallacies)}.")
    if pak["code_switching"]:
        parts.append("Urdu-English code-switching observed.")

    return {"score": sc["final"], "subscores": sc, "counts": counts,
            "avg_sources": avg_sources, "summary": " ".join(parts)}
