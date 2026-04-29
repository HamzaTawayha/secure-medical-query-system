from __future__ import annotations

import math

import pandas as pd

from features import build_live_event_features


ALLOW_THRESHOLD = 4.0
BLOCK_THRESHOLD = 8.0
MAX_RISK_SCORE = 10.0

RULE_WEIGHTS = {
    "unauthorized_role": 10.0,
    "no_relationship": 2.0,
    "after_hours": 1.2,
    "outside_shift": 1.0,
    "single_patient_result": 2.2,
    "small_result_count": 1.4,
    "keyword_present": 1.2,
    "sensitive_keyword": 2.4,
    "sensitive_note_type": 1.4,
    "cross_department": 1.4,
    "post_discharge": 2.2,
    "high_interest_patient": 1.8,
    "recent_event_burst": 1.4,
    "multi_patient_sweep": 1.2,
    "researcher_access": 0.8,
    "billing_clinical_access": 1.4,
}

REASON_MESSAGES = {
    "unauthorized_role": "Role is not authorized by the access policy.",
    "no_relationship": "No active treatment, team, or administrative relationship is present.",
    "after_hours": "Access occurred during late-night or early-morning hours.",
    "outside_shift": "Access occurred outside the user's normal shift window.",
    "single_patient_result": "Query returned a single patient, increasing re-identification risk.",
    "small_result_count": "Query returned a very small patient cohort.",
    "keyword_present": "Free-text keyword search was used.",
    "sensitive_keyword": "Keyword matches a sensitive-topic list.",
    "sensitive_note_type": "Access involves a sensitive note category.",
    "cross_department": "User department differs from the patient encounter department.",
    "post_discharge": "Access occurred after the care relationship or encounter window ended.",
    "high_interest_patient": "Patient is marked as high-interest in the synthetic benchmark.",
    "recent_event_burst": "User has an unusually dense recent access pattern.",
    "multi_patient_sweep": "Query returns a large cohort consistent with sweeping behavior.",
    "researcher_access": "Researcher role is treated as higher review priority for identifiable access.",
    "billing_clinical_access": "Billing role is accessing clinically sensitive context.",
}


def calculate_rule_risk(
    query_input: dict | None = None,
    result_count: int | None = None,
    features: dict | pd.Series | pd.DataFrame | None = None,
    previous_queries=None,
) -> dict:
    row = _coerce_feature_row(query_input=query_input, result_count=result_count, features=features)
    score = 0.0
    reasons = []

    def add(code: str, condition: bool, multiplier: float = 1.0):
        nonlocal score
        if condition:
            weight = RULE_WEIGHTS[code] * multiplier
            score += weight
            reasons.append(
                {
                    "code": code,
                    "weight": round(weight, 2),
                    "message": REASON_MESSAGES[code],
                }
            )

    add("unauthorized_role", _value(row, "is_authorized_role") == 0)
    add("no_relationship", _value(row, "no_relationship") == 1)
    add("after_hours", _value(row, "after_hours") == 1)
    add("outside_shift", _value(row, "outside_shift") == 1)
    add("single_patient_result", _value(row, "single_patient_result") == 1)
    add("small_result_count", _value(row, "small_result_count") == 1 and _value(row, "single_patient_result") == 0)
    add("keyword_present", _value(row, "keyword_present") == 1)
    add("sensitive_keyword", _value(row, "sensitive_keyword_flag") == 1)
    add("sensitive_note_type", _value(row, "note_type_sensitive") == 1)
    add("cross_department", _value(row, "cross_department_access") == 1)
    add("post_discharge", _value(row, "post_discharge_access") == 1)
    add("high_interest_patient", _value(row, "high_interest_patient") == 1)
    add("recent_event_burst", _value(row, "recent_user_event_count_1h") >= 6)
    add("multi_patient_sweep", _value(row, "result_count") >= 50)
    add("researcher_access", _value(row, "is_researcher") == 1 and _value(row, "keyword_present") == 1)
    add("billing_clinical_access", _value(row, "is_billing") == 1 and _value(row, "note_type_sensitive") == 1)

    if previous_queries:
        score += 0.8
        reasons.append(
            {
                "code": "previous_query_context",
                "weight": 0.8,
                "message": "Previous query context was supplied for the same user/session.",
            }
        )

    score = min(MAX_RISK_SCORE, max(0.0, score))
    decision = decide_action(score)
    return {
        "risk_score": round(score, 2),
        "risk_probability": score_to_probability(score),
        "decision": decision,
        "reason_codes": reasons,
        "decision_reason": summarize_reasons(reasons, default="Rule score did not trigger any high-risk condition."),
        "review_priority": review_priority(score),
    }


def calculate_risk(query_input, result_count, previous_queries=None):
    return calculate_rule_risk(
        query_input=query_input,
        result_count=result_count,
        previous_queries=previous_queries,
    )["risk_score"]


def decide_action(risk_score):
    if risk_score >= BLOCK_THRESHOLD:
        return "BLOCK"
    if risk_score >= ALLOW_THRESHOLD:
        return "FLAG"
    return "ALLOW"


def score_to_probability(risk_score: float) -> float:
    value = max(0.0, min(MAX_RISK_SCORE, float(risk_score)))
    return round(value / MAX_RISK_SCORE, 4)


def review_priority(risk_score: float) -> str:
    if risk_score >= BLOCK_THRESHOLD:
        return "urgent"
    if risk_score >= 6:
        return "high"
    if risk_score >= ALLOW_THRESHOLD:
        return "medium"
    return "low"


def summarize_reasons(reasons: list[dict], default: str = "") -> str:
    if not reasons:
        return default
    messages = [reason["message"] for reason in sorted(reasons, key=lambda item: item["weight"], reverse=True)[:3]]
    return " ".join(messages)


def _coerce_feature_row(
    query_input: dict | None,
    result_count: int | None,
    features: dict | pd.Series | pd.DataFrame | None,
):
    if features is None:
        feature_frame = build_live_event_features(query_input or {}, result_count)
        return feature_frame.iloc[0]
    if isinstance(features, pd.DataFrame):
        return features.iloc[0]
    if isinstance(features, pd.Series):
        return features
    return pd.Series(features)


def _value(row, key: str, default=0):
    value = row.get(key, default)
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    return value
