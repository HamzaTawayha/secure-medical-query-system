import pandas as pd

from features import FEATURE_COLUMNS, build_event_features


def test_feature_extraction_handles_temporal_context_and_recent_counts():
    events = pd.DataFrame(
        [
            {
                "event_id": "A1",
                "timestamp": "2026-01-05T02:00:00",
                "user_id": "U1",
                "role": "researcher",
                "user_department": "research",
                "patient_id": "P1",
                "patient_department": "neurology",
                "query_type": "keyword_search",
                "note_type": "psychiatry",
                "keyword": "hippocampus",
                "result_count": 1,
                "relationship_match": False,
                "discharge_time": "2026-01-04T12:00:00",
            },
            {
                "event_id": "A2",
                "timestamp": "2026-01-05T02:30:00",
                "user_id": "U1",
                "role": "researcher",
                "user_department": "research",
                "patient_id": "P2",
                "patient_department": "neurology",
                "query_type": "chart_view",
                "note_type": "progress",
                "keyword": "",
                "result_count": 12,
                "relationship_match": True,
                "discharge_time": "2026-01-06T12:00:00",
            },
        ]
    )

    features = build_event_features(events)

    for column in FEATURE_COLUMNS:
        assert column in features.columns
    assert features.loc[0, "after_hours"] == 1
    assert features.loc[0, "post_discharge_access"] == 1
    assert features.loc[0, "sensitive_keyword_flag"] == 1
    assert features.loc[1, "recent_user_event_count_1h"] == 1
    assert features.loc[1, "recent_user_patient_count_1h"] == 1
