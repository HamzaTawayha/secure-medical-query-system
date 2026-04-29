from risk_engine import calculate_rule_risk, decide_action


def test_rule_risk_returns_score_and_reason_codes():
    result = calculate_rule_risk(
        features={
            "is_authorized_role": 1,
            "no_relationship": 1,
            "after_hours": 1,
            "outside_shift": 0,
            "single_patient_result": 1,
            "small_result_count": 1,
            "keyword_present": 1,
            "sensitive_keyword_flag": 1,
            "note_type_sensitive": 1,
            "cross_department_access": 1,
            "post_discharge_access": 0,
            "high_interest_patient": 0,
            "recent_user_event_count_1h": 0,
            "result_count": 1,
            "is_researcher": 1,
            "is_billing": 0,
        }
    )

    assert result["risk_score"] >= 8
    assert result["decision"] == "BLOCK"
    assert any(reason["code"] == "sensitive_keyword" for reason in result["reason_codes"])


def test_decide_action_thresholds():
    assert decide_action(1.5) == "ALLOW"
    assert decide_action(4.0) == "FLAG"
    assert decide_action(8.0) == "BLOCK"
