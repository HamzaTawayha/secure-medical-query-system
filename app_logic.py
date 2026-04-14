from datetime import datetime
from db_sql import query_patients
from db_cosmos import search_notes, log_query
from risk_engine import calculate_risk, decide_action


def run_secure_query(role="researcher", age_min=None, diagnosis=None, outcome=None, keyword=None):
    query_input = {
        "role": role,
        "age_min": age_min,
        "diagnosis": diagnosis,
        "outcome": outcome,
        "keyword": keyword
    }

    patients = query_patients(
        age_min=age_min,
        diagnosis=diagnosis,
        outcome=outcome
    )

    result_count = len(patients)
    risk_score = calculate_risk(query_input, result_count)
    decision = decide_action(risk_score)

    result = {
        "query_input": query_input,
        "risk_score": risk_score,
        "decision": decision,
        "patients": [],
        "notes": [],
        "log_id": None
    }

    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "query_input": query_input,
        "risk_score": risk_score,
        "decision": decision,
        "sql_result_count": result_count
    }

    inserted_log_id = log_query(log_data)
    result["log_id"] = inserted_log_id

    if decision == "BLOCK":
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