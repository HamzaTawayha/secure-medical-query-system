from datetime import datetime, timezone
from baselines import normalize_decision_mode, score_event
from db_sql import query_patients
from db_cosmos import search_notes, log_query
from features import build_live_event_features
from ml_model import load_model


def run_secure_query(
    role="researcher",
    age_min=None,
    diagnosis=None,
    outcome=None,
    keyword=None,
    decision_mode="rule_based",
    k_threshold=3,
):
    decision_mode = normalize_decision_mode(decision_mode)

    query_input = {
        "role": role,
        "age_min": age_min,
        "diagnosis": diagnosis,
        "outcome": outcome,
        "keyword": keyword
    }

    result = {
        "decision_mode": decision_mode,
        "query_input": query_input,
        "risk_score": None,
        "risk_probability": None,
        "decision": None,
        "decision_reason": None,
        "reason_codes": [],
        "review_priority": None,
        "baseline_scores": {},
        "k_threshold": k_threshold,
        "patients": [],
        "notes": [],
        "log_id": None
    }

    if decision_mode == "rbac":
        feature_row = build_live_event_features(query_input, result_count=0).iloc[0]
        scored = score_event(feature_row, mode="rbac", k_threshold=k_threshold)
        _apply_scored_result(result, scored)

        if scored["decision"] == "BLOCK":
            result["log_id"] = _log_result(result, sql_result_count=None)
            return result

    patients = query_patients(
        age_min=age_min,
        diagnosis=diagnosis,
        outcome=outcome
    )

    result_count = len(patients)
    if decision_mode != "rbac":
        feature_row = build_live_event_features(query_input, result_count=result_count).iloc[0]
        model_bundle = load_model() if decision_mode in {"ml_only", "hybrid"} else None
        scored = score_event(
            feature_row,
            mode=decision_mode,
            model_bundle=model_bundle,
            k_threshold=k_threshold,
        )
        _apply_scored_result(result, scored)

    result["log_id"] = _log_result(result, sql_result_count=result_count)

    if result["decision"] == "BLOCK":
        return result

    for patient in patients:
        result["patients"].append({
            "patient_id": patient[0],
            "age": patient[1],
            "gender": patient[2],
            "diagnosis": patient[3],
            "outcome": patient[4]
        })

    patient_ids = [patient["patient_id"] for patient in result["patients"]]

    notes = search_notes(patient_ids=patient_ids, keyword=keyword)

    for note in notes:
        note_copy = dict(note)
        note_copy.pop("_id", None)
        result["notes"].append(note_copy)

    return result


def _apply_scored_result(result, scored):
    result["risk_score"] = scored["risk_score"]
    result["risk_probability"] = scored["risk_probability"]
    result["decision"] = scored["decision"]
    result["decision_reason"] = scored["decision_reason"]
    result["reason_codes"] = scored.get("reason_codes", [])
    result["review_priority"] = scored.get("review_priority")
    result["baseline_scores"] = scored.get("baseline_scores", {})


def _log_result(result, sql_result_count):
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision_mode": result["decision_mode"],
        "query_input": result["query_input"],
        "risk_score": result["risk_score"],
        "risk_probability": result["risk_probability"],
        "decision": result["decision"],
        "decision_reason": result["decision_reason"],
        "reason_codes": result["reason_codes"],
        "review_priority": result["review_priority"],
        "baseline_scores": result["baseline_scores"],
        "k_threshold": result["k_threshold"],
        "sql_result_count": sql_result_count,
    }
    return log_query(log_data)
