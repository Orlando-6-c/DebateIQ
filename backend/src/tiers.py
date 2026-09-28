"""Subscription tiers: limits + feature gates. Single source of truth."""

TIERS = {
    "free": {"label": "Free", "price": "Rs 0",
             "word_cap": 300, "audio_sec": 60, "monthly_analyses": 25,
             "judge_mode": False, "history": False,
             "blurb": "For trying it out and single speeches."},
    "pro": {"label": "Pro", "price": "Rs 1,500/mo",
            "word_cap": 2000, "audio_sec": 300, "monthly_analyses": None,
            "judge_mode": True, "history": True,
            "blurb": "For debaters, coaches and journalists."},
    "org": {"label": "Org", "price": "Rs 9,000/mo",
            "word_cap": 6000, "audio_sec": 900, "monthly_analyses": None,
            "judge_mode": True, "history": True,
            "blurb": "For MUN circuits, universities and fact-check desks."},
}


def get(tier):
    return TIERS.get(tier, TIERS["free"])
