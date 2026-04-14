def calculate_risk(query_input, result_count, previous_queries=None):
    risk_score = 0

    role = query_input.get("role")
    diagnosis = query_input.get("diagnosis")
    outcome = query_input.get("outcome")
    age_min = query_input.get("age_min")
    keyword = query_input.get("keyword")

    # Base query sensitivity
    if diagnosis:
        risk_score += 1

    if outcome:
        risk_score += 1

    if age_min is not None:
        risk_score += 1

    if keyword:
        risk_score += 4

    # Result-size risk
    if result_count == 1:
        risk_score += 4
    elif result_count <= 3:
        risk_score += 2
    elif result_count <= 5:
        risk_score += 1

    # Role adjustment
    if role == "doctor":
        risk_score -= 2
    elif role == "researcher":
        risk_score += 1

    # Repeated behavior
    if previous_queries:
        risk_score += 1

    if risk_score < 0:
        risk_score = 0

    return risk_score


def decide_action(risk_score):
    if risk_score >= 8:
        return "BLOCK"
    elif risk_score >= 4:
        return "FLAG"
    return "ALLOW"