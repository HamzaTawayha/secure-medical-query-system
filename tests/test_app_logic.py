import app_logic


def test_run_secure_query_returns_stable_risk_fields(monkeypatch):
    patients = [(idx, 30 + idx, "F", "epilepsy", "stable") for idx in range(1, 13)]

    monkeypatch.setattr(app_logic, "query_patients", lambda age_min=None, diagnosis=None, outcome=None: patients)
    monkeypatch.setattr(
        app_logic,
        "search_notes",
        lambda patient_ids, keyword=None: [{"_id": "mongo-id", "patient_id": patient_ids[0], "note_text": "routine note"}],
    )
    monkeypatch.setattr(app_logic, "log_query", lambda log_data: "log-123")
    monkeypatch.setattr(app_logic, "load_model", lambda: None)

    result = app_logic.run_secure_query(
        role="doctor",
        age_min=20,
        diagnosis="epilepsy",
        keyword=None,
        decision_mode="hybrid",
    )

    assert result["log_id"] == "log-123"
    assert result["risk_score"] is not None
    assert result["risk_probability"] is not None
    assert result["review_priority"] in {"low", "medium", "high", "urgent"}
    assert isinstance(result["reason_codes"], list)
    assert isinstance(result["baseline_scores"], dict)
    assert result["patients"]
    assert "_id" not in result["notes"][0]


def test_k_anonymity_blocks_small_result_set(monkeypatch):
    monkeypatch.setattr(app_logic, "query_patients", lambda age_min=None, diagnosis=None, outcome=None: [(1, 44, "M", "stroke", "poor")])
    monkeypatch.setattr(app_logic, "search_notes", lambda patient_ids, keyword=None: [])
    monkeypatch.setattr(app_logic, "log_query", lambda log_data: "log-456")

    result = app_logic.run_secure_query(role="researcher", decision_mode="k_anonymity", k_threshold=3)

    assert result["decision"] == "BLOCK"
    assert result["patients"] == []
    assert result["log_id"] == "log-456"
