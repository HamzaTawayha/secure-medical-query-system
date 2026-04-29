from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


AUTHORIZED_ROLES = {"doctor", "nurse", "researcher", "pharmacist", "billing", "compliance"}
CLINICAL_ROLES = {"doctor", "nurse", "pharmacist"}
SENSITIVE_KEYWORDS = {"hippocampus", "substance", "psychiatric", "genetic", "celebrity", "pregnancy"}
SENSITIVE_NOTE_TYPES = {"psychiatry", "social", "genetics"}

FEATURE_COLUMNS = [
    "is_authorized_role",
    "is_clinical_role",
    "is_researcher",
    "is_billing",
    "relationship_match",
    "no_relationship",
    "after_hours",
    "outside_shift",
    "result_count",
    "small_result_count",
    "single_patient_result",
    "keyword_present",
    "sensitive_keyword_flag",
    "note_type_sensitive",
    "cross_department_access",
    "post_discharge_access",
    "high_interest_patient",
    "recent_user_event_count_1h",
    "recent_user_patient_count_1h",
    "query_type_keyword_search",
    "query_type_cohort_query",
    "query_type_note_view",
    "query_specificity",
]

TEMPORAL_FEATURES = [
    "after_hours",
    "outside_shift",
    "post_discharge_access",
    "recent_user_event_count_1h",
    "recent_user_patient_count_1h",
]

CONTEXT_FEATURES = [
    "is_authorized_role",
    "is_clinical_role",
    "is_researcher",
    "is_billing",
    "relationship_match",
    "no_relationship",
    "cross_department_access",
    "high_interest_patient",
]

TEXT_FEATURES = [
    "keyword_present",
    "sensitive_keyword_flag",
    "note_type_sensitive",
    "query_type_keyword_search",
]


def build_event_features(
    events: pd.DataFrame,
    patients: pd.DataFrame | None = None,
    encounters: pd.DataFrame | None = None,
    users: pd.DataFrame | None = None,
    relationships: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frame = events.copy()
    frame = _merge_context(frame, patients=patients, encounters=encounters, users=users)
    frame["timestamp"] = pd.to_datetime(frame.get("timestamp", pd.Timestamp.now(tz="UTC")), errors="coerce")

    if "relationship_match" not in frame.columns and relationships is not None:
        frame["relationship_match"] = _compute_relationship_match(frame, relationships)
    elif "relationship_match" not in frame.columns:
        frame["relationship_match"] = False

    frame["role"] = frame.get("role", "").fillna("").astype(str)
    frame["user_department"] = frame.get("user_department", "").fillna("").astype(str)
    frame["patient_department"] = frame.get("patient_department", "").fillna("").astype(str)
    frame["keyword"] = frame.get("keyword", "").fillna("").astype(str)
    frame["note_type"] = frame.get("note_type", "").fillna("").astype(str)
    frame["query_type"] = frame.get("query_type", "").fillna("").astype(str)
    frame["result_count"] = pd.to_numeric(frame.get("result_count", 0), errors="coerce").fillna(0)

    features = pd.DataFrame(index=frame.index)
    if "event_id" in frame.columns:
        features["event_id"] = frame["event_id"]

    features["is_authorized_role"] = frame["role"].isin(AUTHORIZED_ROLES).astype(int)
    features["is_clinical_role"] = frame["role"].isin(CLINICAL_ROLES).astype(int)
    features["is_researcher"] = (frame["role"] == "researcher").astype(int)
    features["is_billing"] = (frame["role"] == "billing").astype(int)
    features["relationship_match"] = frame["relationship_match"].astype(bool).astype(int)
    features["no_relationship"] = (1 - features["relationship_match"]).clip(lower=0)
    features["after_hours"] = frame["timestamp"].dt.hour.isin([22, 23, 0, 1, 2, 3, 4, 5]).astype(int)
    features["outside_shift"] = _outside_shift(frame).astype(int)
    features["result_count"] = frame["result_count"].clip(lower=0, upper=200)
    features["small_result_count"] = (frame["result_count"] <= 3).astype(int)
    features["single_patient_result"] = (frame["result_count"] == 1).astype(int)
    features["keyword_present"] = (frame["keyword"].str.len() > 0).astype(int)
    features["sensitive_keyword_flag"] = frame["keyword"].str.lower().isin(SENSITIVE_KEYWORDS).astype(int)
    features["note_type_sensitive"] = frame["note_type"].str.lower().isin(SENSITIVE_NOTE_TYPES).astype(int)
    features["cross_department_access"] = (
        (frame["user_department"].str.len() > 0)
        & (frame["patient_department"].str.len() > 0)
        & (frame["user_department"] != frame["patient_department"])
    ).astype(int)
    features["post_discharge_access"] = _post_discharge(frame).astype(int)
    features["high_interest_patient"] = _bool_series(frame.get("high_interest_patient", False), frame.index).astype(int)
    features["recent_user_event_count_1h"] = _recent_user_counts(frame, unique_patients=False)
    features["recent_user_patient_count_1h"] = _recent_user_counts(frame, unique_patients=True)
    features["query_type_keyword_search"] = (frame["query_type"] == "keyword_search").astype(int)
    features["query_type_cohort_query"] = (frame["query_type"] == "cohort_query").astype(int)
    features["query_type_note_view"] = (frame["query_type"] == "note_view").astype(int)
    features["query_specificity"] = (
        features["small_result_count"]
        + features["keyword_present"]
        + features["note_type_sensitive"]
        + features["single_patient_result"]
    )

    for column in FEATURE_COLUMNS:
        if column not in features.columns:
            features[column] = 0

    passthrough = [
        "label",
        "scenario",
        "risk_tier",
        "timestamp",
        "user_id",
        "patient_id",
        "role",
        "query_type",
    ]
    for column in passthrough:
        if column in frame.columns:
            features[column] = frame[column].values

    return features


def build_live_event_features(
    query_input: dict,
    result_count: int | None,
    context: dict | None = None,
) -> pd.DataFrame:
    context = context or {}
    role = query_input.get("role") or "researcher"
    diagnosis = query_input.get("diagnosis") or ""
    keyword = query_input.get("keyword") or ""
    user_department = context.get("user_department") or _default_department_for_role(role, diagnosis)
    patient_department = context.get("patient_department") or _default_department_for_diagnosis(diagnosis)
    timestamp = context.get("timestamp") or datetime.now(timezone.utc).isoformat()

    event = {
        "event_id": context.get("event_id", "live-query"),
        "timestamp": timestamp,
        "user_id": context.get("user_id", f"live-{role}"),
        "role": role,
        "user_department": user_department,
        "patient_id": context.get("patient_id", "live-cohort"),
        "patient_department": patient_department,
        "diagnosis": diagnosis,
        "outcome": query_input.get("outcome") or "",
        "query_type": "keyword_search" if keyword else "cohort_query",
        "note_type": context.get("note_type", "progress"),
        "keyword": keyword,
        "result_count": 0 if result_count is None else result_count,
        "relationship_match": context.get("relationship_match", role in CLINICAL_ROLES),
        "high_interest_patient": context.get("high_interest_patient", False),
    }
    return build_event_features(pd.DataFrame([event]))


def zero_feature_group(features: pd.DataFrame, group: str) -> pd.DataFrame:
    frame = features.copy()
    groups = {
        "temporal": TEMPORAL_FEATURES,
        "context": CONTEXT_FEATURES,
        "text": TEXT_FEATURES,
    }
    for column in groups.get(group, []):
        if column in frame.columns:
            frame[column] = 0
    return frame


def _merge_context(
    events: pd.DataFrame,
    patients: pd.DataFrame | None,
    encounters: pd.DataFrame | None,
    users: pd.DataFrame | None,
) -> pd.DataFrame:
    frame = events.copy()
    if users is not None and "user_id" in frame.columns:
        user_columns = [column for column in ["user_id", "role", "department", "shift_start_hour", "shift_length_hours"] if column in users.columns]
        user_context = users[user_columns].rename(columns={"department": "user_department"})
        frame = frame.merge(user_context, on="user_id", how="left", suffixes=("", "_user"))
        frame["role"] = frame.get("role", frame.get("role_user", "")).fillna(frame.get("role_user", ""))
        frame["user_department"] = frame.get("user_department", frame.get("user_department_user", "")).fillna(
            frame.get("user_department_user", "")
        )

    if patients is not None and "patient_id" in frame.columns:
        patient_columns = [
            column
            for column in ["patient_id", "department", "discharge_time", "high_interest_patient"]
            if column in patients.columns
        ]
        patient_context = patients[patient_columns].rename(columns={"department": "patient_department"})
        frame = frame.merge(patient_context, on="patient_id", how="left", suffixes=("", "_patient"))
        if "patient_department_patient" in frame.columns:
            frame["patient_department"] = frame.get("patient_department", "").fillna(frame["patient_department_patient"])
        if "discharge_time_patient" in frame.columns:
            frame["discharge_time"] = frame.get("discharge_time", pd.NaT).fillna(frame["discharge_time_patient"])
        if "high_interest_patient_patient" in frame.columns:
            frame["high_interest_patient"] = frame.get("high_interest_patient", False).fillna(
                frame["high_interest_patient_patient"]
            )

    if encounters is not None and "encounter_id" in frame.columns:
        encounter_columns = [
            column
            for column in ["encounter_id", "department", "discharge_time"]
            if column in encounters.columns
        ]
        encounter_context = encounters[encounter_columns].rename(columns={"department": "patient_department"})
        frame = frame.merge(encounter_context, on="encounter_id", how="left", suffixes=("", "_encounter"))
        if "patient_department_encounter" in frame.columns:
            frame["patient_department"] = frame.get("patient_department", "").fillna(frame["patient_department_encounter"])
        if "discharge_time_encounter" in frame.columns:
            frame["discharge_time"] = frame.get("discharge_time", pd.NaT).fillna(frame["discharge_time_encounter"])

    return frame


def _compute_relationship_match(events: pd.DataFrame, relationships: pd.DataFrame) -> pd.Series:
    relationships = relationships.copy()
    relationships["start_time"] = pd.to_datetime(relationships["start_time"], errors="coerce")
    relationships["end_time"] = pd.to_datetime(relationships["end_time"], errors="coerce")
    matches = []
    for _, event in events.iterrows():
        related = relationships[
            (relationships["user_id"] == event.get("user_id"))
            & (relationships["patient_id"] == event.get("patient_id"))
            & (relationships["start_time"] <= event.get("timestamp"))
            & (relationships["end_time"] >= event.get("timestamp"))
        ]
        matches.append(not related.empty)
    return pd.Series(matches, index=events.index)


def _outside_shift(frame: pd.DataFrame) -> pd.Series:
    if "shift_start_hour" not in frame.columns or "shift_length_hours" not in frame.columns:
        return pd.Series(False, index=frame.index)

    hour = frame["timestamp"].dt.hour
    start = pd.to_numeric(frame["shift_start_hour"], errors="coerce").fillna(8).astype(int)
    length = pd.to_numeric(frame["shift_length_hours"], errors="coerce").fillna(10).astype(int)
    end = (start + length) % 24
    inside = []
    for current_hour, start_hour, end_hour in zip(hour, start, end):
        if start_hour <= end_hour:
            inside.append(start_hour <= current_hour < end_hour)
        else:
            inside.append(current_hour >= start_hour or current_hour < end_hour)
    return ~pd.Series(inside, index=frame.index)


def _post_discharge(frame: pd.DataFrame) -> pd.Series:
    if "discharge_time" not in frame.columns:
        return pd.Series(False, index=frame.index)
    discharge = pd.to_datetime(frame["discharge_time"], errors="coerce")
    return frame["timestamp"] > discharge


def _recent_user_counts(frame: pd.DataFrame, unique_patients: bool) -> pd.Series:
    if "user_id" not in frame.columns:
        return pd.Series(0, index=frame.index)

    ordered = frame[["timestamp", "user_id", "patient_id"]].copy() if "patient_id" in frame.columns else frame[["timestamp", "user_id"]].copy()
    ordered["_original_index"] = frame.index
    ordered = ordered.sort_values("timestamp")
    counts = pd.Series(0, index=frame.index, dtype=float)

    for _, group in ordered.groupby("user_id", sort=False):
        timestamps = list(group["timestamp"])
        patients = list(group.get("patient_id", pd.Series([""] * len(group))))
        original_indices = list(group["_original_index"])
        for position, timestamp in enumerate(timestamps):
            lower = timestamp - pd.Timedelta(hours=1)
            previous_positions = [idx for idx, value in enumerate(timestamps[:position]) if value >= lower]
            if unique_patients:
                counts.loc[original_indices[position]] = len({patients[idx] for idx in previous_positions})
            else:
                counts.loc[original_indices[position]] = len(previous_positions)
    return counts


def _bool_series(value, index: pd.Index) -> pd.Series:
    if isinstance(value, pd.Series):
        return value.fillna(False).astype(bool)
    return pd.Series(value, index=index).fillna(False).astype(bool)


def _default_department_for_role(role: str, diagnosis: str) -> str:
    if role == "researcher":
        return "research"
    if role == "billing":
        return "billing"
    return _default_department_for_diagnosis(diagnosis)


def _default_department_for_diagnosis(diagnosis: str) -> str:
    return {
        "epilepsy": "neurology",
        "stroke": "neurology",
        "heart failure": "cardiology",
        "depression": "psychiatry",
        "cancer": "oncology",
    }.get(str(diagnosis).lower(), "ED")
