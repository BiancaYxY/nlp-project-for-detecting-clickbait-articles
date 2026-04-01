from typing import Dict


# ── Thresholds ────────────────────────────────────────────────────────────────

SIMILARITY_HIGH = 0.55
SIMILARITY_LOW = 0.30

CLICKBAIT_HIGH = 0.65
CLICKBAIT_LOW = 0.35

# ── Verdict labels ────────────────────────────────────────────────────────────

VERDICT_RELIABLE = "reliable"
VERDICT_MISLEADING = "misleading"
VERDICT_CLICKBAIT = "clickbait"
VERDICT_UNVERIFIABLE = "unverifiable"


# ── Scoring weights ───────────────────────────────────────────────────────────
# similarity: 35%  |  entailment: 40%  |  clickbait: 25%

W_SIMILARITY = 0.35
W_ENTAILMENT = 0.40
W_CLICKBAIT = 0.25

ENTAILMENT_SCORES = {
    "entailment": 1.0,
    "neutral": 0.5,
    "contradiction": 0.0,
}


def _entailment_to_score(label: str) -> float:
    return ENTAILMENT_SCORES.get((label or "").lower(), 0.5)


def _clickbait_to_penalty(final_score: float) -> float:
    """
    Converts clickbait final_score to a 0-1 'trust' value.
    High clickbait score → low trust.
    """
    return round(1.0 - final_score, 4)


def compute_verdict(
    similarity_result: Dict,
    entailment_result: Dict,
    clickbait_result: Dict,
) -> Dict:
    """
    Aggregates the three NLP signals into a final verdict.

    Returns
    -------
    {
        "verdict":        str,   # reliable | misleading | clickbait | unverifiable
        "confidence":     float, # weighted composite score  [0.0 – 1.0]
        "signals": {
            "similarity_score":  float,
            "entailment_label":  str,
            "entailment_score":  float,
            "clickbait_label":   str,
            "clickbait_score":   float,
        },
        "flags": [str],          # human-readable list of raised concerns
    }
    """

    sim_score = float(similarity_result.get("similarity_score", 0.0))
    sim_status = similarity_result.get("status", "ok")

    ent_label = entailment_result.get("label") or "neutral"
    ent_status = entailment_result.get("status", "ok")

    cb_label = clickbait_result.get("label") or "not_clickbait"
    cb_score = float(clickbait_result.get("final_score", 0.0))
    cb_status = clickbait_result.get("status", "ok")

    all_missing = all(
        s == "missing_input"
        for s in [sim_status, ent_status, cb_status]
    )
    if all_missing:
        return {
            "verdict": VERDICT_UNVERIFIABLE,
            "confidence": 0.0,
            "signals": {},
            "flags": ["Insufficient data — headline or article text is empty."],
        }

    ent_score = _entailment_to_score(ent_label)
    cb_trust = _clickbait_to_penalty(cb_score)

    confidence = round(
        W_SIMILARITY * sim_score
        + W_ENTAILMENT * ent_score
        + W_CLICKBAIT * cb_trust,
        4,
    )

    flags = []

    if sim_score < SIMILARITY_LOW:
        flags.append("Headline topic is largely unrelated to the article content.")
    elif sim_score < SIMILARITY_HIGH:
        flags.append("Headline is only partially related to the article content.")

    if ent_label == "contradiction":
        flags.append("Article content contradicts the headline claim.")
    elif ent_label == "neutral":
        flags.append("Article content neither confirms nor contradicts the headline.")

    if cb_score >= CLICKBAIT_HIGH:
        flags.append("Headline shows strong clickbait signals.")
    elif cb_score >= CLICKBAIT_LOW:
        flags.append("Headline shows moderate clickbait signals.")

    if ent_label == "contradiction" and sim_score < SIMILARITY_HIGH:
        verdict = VERDICT_MISLEADING

    elif cb_score >= CLICKBAIT_HIGH and ent_label != "entailment":
        verdict = VERDICT_CLICKBAIT

    elif sim_score < SIMILARITY_LOW and ent_label in ("neutral", "contradiction"):
        verdict = VERDICT_MISLEADING

    elif confidence >= 0.65:
        verdict = VERDICT_RELIABLE

    elif confidence >= 0.40:
        verdict = VERDICT_CLICKBAIT if cb_score >= CLICKBAIT_LOW else VERDICT_MISLEADING

    else:
        verdict = VERDICT_MISLEADING

    return {
        "verdict": verdict,
        "confidence": confidence,
        "signals": {
            "similarity_score": round(sim_score, 4),
            "entailment_label": ent_label,
            "entailment_score": round(ent_score, 4),
            "clickbait_label": cb_label,
            "clickbait_score": round(cb_score, 4),
        },
        "flags": flags,
    }