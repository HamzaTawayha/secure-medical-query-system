from __future__ import annotations

import pandas as pd

from features import AUTHORIZED_ROLES, FEATURE_COLUMNS
from risk_engine import decide_action, review_priority, score_to_probability, summarize_reasons
from risk_engine import calculate_rule_risk


SUPPORTED_DECISION_MODES = {
    "rbac": "RBAC baseline",
    "rule_based": "Rule-based baseline",
    "ml_only": "ML-only baseline",
    "hybrid": "Hybrid triage",
    "k_anonymity": "k-anonymity baseline",
}

CORE_BASELINE_MODES = ["rbac", "rule_based", "ml_only", "hybrid"]


def normalize_decision_mode(decision_mode):
    if decision_mode in SUPPORTED_DECISION_MODES:
        return decision_mode
    return "rule_based"


def decide_rbac(query_input):
    role = query_input.get("role")
    if role in AUTHORIZED_ROLES:
        return _result(
            mode="rbac",
            risk_score=0.0,
            reason_codes=[
                {
                    "code": "role_authorized",
                    "weight": 0.0,
                    "message": "Role is authorized. RBAC does not inspect query specificity, keyword use, or result size.",
                }
            ],
        )

    return _result(
        mode="rbac",
        risk_score=10.0,
        reason_codes=[
            {
                "code": "unauthorized_role",
                "weight": 10.0,
                "message": "Role is not authorized by the RBAC policy.",
            }
        ],
    )


def decide_k_anonymity(result_count, k_threshold=3):
    if result_count < k_threshold:
        return _result(
            mode="k_anonymity",
            risk_score=10.0,
            reason_codes=[
                {
                    "code": "below_k_threshold",
                    "weight": 10.0,
                    "message": f"Result count is {result_count}, which is below the k-anonymity threshold of {k_threshold}.",
                }
            ],
        )

    return _result(
        mode="k_anonymity",
        risk_score=0.0,
        reason_codes=[
            {
                "code": "meets_k_threshold",
                "weight": 0.0,
                "message": f"Result count is {result_count}, which meets the k-anonymity threshold of {k_threshold}.",
            }
        ],
    )


def score_event(
    features: dict | pd.Series,
    mode: str,
    model_bundle=None,
    k_threshold: int = 3,
) -> dict:
    mode = normalize_decision_mode(mode)
    row = pd.Series(features)

    if mode == "rbac":
        return _score_rbac_row(row)
    if mode == "rule_based":
        rule_result = calculate_rule_risk(features=row)
        return _with_mode(rule_result, "rule_based", {"rule_based": rule_result["risk_score"]})
    if mode == "ml_only":
        return _score_ml_row(row, model_bundle=model_bundle)
    if mode == "hybrid":
        return _score_hybrid_row(row, model_bundle=model_bundle)
    if mode == "k_anonymity":
        return decide_k_anonymity(int(row.get("result_count", 0)), k_threshold=k_threshold)

    return _score_rule_row(row)


def score_feature_frame(
    feature_frame: pd.DataFrame,
    mode: str,
    model_bundle=None,
    k_threshold: int = 3,
) -> pd.DataFrame:
    rows = []
    for _, row in feature_frame.iterrows():
        scored = score_event(row, mode=mode, model_bundle=model_bundle, k_threshold=k_threshold)
        rows.append(
            {
                "event_id": row.get("event_id"),
                "mode": mode,
                "risk_score": scored["risk_score"],
                "risk_probability": scored["risk_probability"],
                "decision": scored["decision"],
                "review_priority": scored["review_priority"],
                "decision_reason": scored["decision_reason"],
                "reason_codes": "|".join(reason["code"] for reason in scored.get("reason_codes", [])),
            }
        )
    return pd.DataFrame(rows)


def _score_rbac_row(row: pd.Series) -> dict:
    risk_score = 0.0 if int(row.get("is_authorized_role", 0)) == 1 else 10.0
    reasons = [
        {
            "code": "role_authorized" if risk_score == 0 else "unauthorized_role",
            "weight": risk_score,
            "message": (
                "Role is authorized. RBAC does not inspect query specificity, keyword use, or result size."
                if risk_score == 0
                else "Role is not authorized by the RBAC policy."
            ),
        }
    ]
    return _result("rbac", risk_score=risk_score, reason_codes=reasons, baseline_scores={"rbac": risk_score})


def _score_rule_row(row: pd.Series) -> dict:
    rule_result = calculate_rule_risk(features=row)
    return _with_mode(rule_result, "rule_based", {"rule_based": rule_result["risk_score"]})


def _score_ml_row(row: pd.Series, model_bundle=None) -> dict:
    from ml_model import predict_probability

    feature_frame = pd.DataFrame([{column: row.get(column, 0) for column in FEATURE_COLUMNS}])
    probability = float(predict_probability(feature_frame, model_bundle=model_bundle)[0])
    risk_score = round(probability * 10.0, 2)
    reasons = [
        {
            "code": "ml_risk_probability",
            "weight": risk_score,
            "message": "ML model estimated suspicious-access probability.",
        }
    ]
    return _result(
        mode="ml_only",
        risk_score=risk_score,
        risk_probability=round(probability, 4),
        reason_codes=reasons,
        baseline_scores={"ml_only": risk_score},
    )


def _score_hybrid_row(row: pd.Series, model_bundle=None) -> dict:
    rbac = _score_rbac_row(row)
    rule = _score_rule_row(row)
    ml = _score_ml_row(row, model_bundle=model_bundle)

    if rbac["risk_score"] >= 10:
        risk_score = 10.0
    else:
        risk_score = round((0.10 * rbac["risk_score"]) + (0.45 * rule["risk_score"]) + (0.45 * ml["risk_score"]), 2)
        risk_score = max(risk_score, rule["risk_score"] if rule["risk_score"] >= 8 else risk_score)

    reasons = _dedupe_reasons(rule.get("reason_codes", []) + ml.get("reason_codes", []) + rbac.get("reason_codes", []))
    return _result(
        mode="hybrid",
        risk_score=risk_score,
        reason_codes=reasons,
        baseline_scores={
            "rbac": rbac["risk_score"],
            "rule_based": rule["risk_score"],
            "ml_only": ml["risk_score"],
            "hybrid": risk_score,
        },
    )


def _result(
    mode: str,
    risk_score: float,
    reason_codes: list[dict],
    risk_probability: float | None = None,
    baseline_scores: dict | None = None,
) -> dict:
    risk_score = round(float(risk_score), 2)
    risk_probability = score_to_probability(risk_score) if risk_probability is None else round(float(risk_probability), 4)
    return {
        "mode": mode,
        "risk_score": risk_score,
        "risk_probability": risk_probability,
        "decision": decide_action(risk_score),
        "decision_reason": summarize_reasons(reason_codes, default="No high-risk condition was detected."),
        "reason_codes": reason_codes,
        "review_priority": review_priority(risk_score),
        "baseline_scores": baseline_scores or {mode: risk_score},
    }


def _with_mode(result: dict, mode: str, baseline_scores: dict) -> dict:
    output = dict(result)
    output["mode"] = mode
    output["baseline_scores"] = baseline_scores
    return output


def _dedupe_reasons(reasons: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for reason in sorted(reasons, key=lambda item: item.get("weight", 0), reverse=True):
        code = reason.get("code")
        if code in seen:
            continue
        seen.add(code)
        deduped.append(reason)
    return deduped[:6]
