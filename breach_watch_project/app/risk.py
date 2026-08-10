"""Transparent, explainable demonstration risk scoring.

This is a rules-based prototype, not a validated security-risk model.
Scores should not be interpreted as the probability that an account was compromised.
"""

DATA_TYPE_WEIGHTS = {
    "passwords": 35,
    "authentication_tokens": 35,
    "financial_data": 25,
    "health_data": 20,
    "government_ids": 25,
    "personal_information": 15,
    "email_addresses": 10,
    "usernames": 8,
    "unknown": 5,
}


def score_incident(data_types: list[str], description: str = "") -> dict:
    normalized = {item.strip().lower().replace(" ", "_") for item in data_types if item.strip()}
    if not normalized:
        normalized = {"unknown"}

    reasons = []
    score = 10  # baseline for a reported incident
    for item in sorted(normalized):
        weight = DATA_TYPE_WEIGHTS.get(item, DATA_TYPE_WEIGHTS["unknown"])
        score += weight
        if item in DATA_TYPE_WEIGHTS:
            reasons.append(f"Reported data category: {item.replace('_', ' ')} (+{weight})")
        else:
            reasons.append(f"Unrecognized data category '{item}' treated conservatively (+5)")

    lowered = description.lower()
    keyword_rules = [
        (("encryption key", "access token", "session token"), 15, "Description mentions an access/session token or encryption key (+15)"),
        (("large-scale", "millions of records", "mass exposure"), 10, "Description suggests a large-scale exposure (+10)"),
    ]
    for keywords, weight, reason in keyword_rules:
        if any(keyword in lowered for keyword in keywords):
            score += weight
            reasons.append(reason)

    score = min(score, 100)
    if score >= 65:
        level = "High"
    elif score >= 35:
        level = "Medium"
    else:
        level = "Low"

    if not reasons:
        reasons = ["No specific sensitive data categories were provided."]
    return {"risk_score": score, "risk_level": level, "risk_reasons": reasons}
