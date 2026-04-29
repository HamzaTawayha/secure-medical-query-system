from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_OUTPUT_DIR = Path("data") / "benchmark"

ROLES = ["doctor", "nurse", "researcher", "pharmacist", "billing", "compliance"]
DEPARTMENTS = ["ED", "neurology", "cardiology", "oncology", "psychiatry", "billing", "research"]
DIAGNOSES = ["epilepsy", "stroke", "heart failure", "diabetes", "depression", "cancer"]
OUTCOMES = ["stable", "improving", "poor", "critical"]
NOTE_TYPES = ["progress", "medication", "discharge", "psychiatry", "social", "genetics"]
SENSITIVE_KEYWORDS = ["hippocampus", "substance", "psychiatric", "genetic", "celebrity", "pregnancy"]
SCENARIOS = [
    "normal_workflow",
    "cross_department_browsing",
    "after_hours_repeated_access",
    "sensitive_keyword_search",
    "post_relationship_access",
    "multi_patient_sweep",
    "high_interest_patient_curiosity",
    "role_context_mismatch",
]


def generate_benchmark(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int = 42,
    n_patients: int = 350,
    n_users: int = 80,
    n_events: int = 5000,
    suspicious_rate: float = 0.14,
    write_csv: bool = True,
) -> dict[str, pd.DataFrame]:
    """Generate a deterministic synthetic EHR access-risk benchmark."""
    rng = np.random.default_rng(seed)
    output_dir = Path(output_dir)
    start = pd.Timestamp("2026-01-01 00:00:00")

    patients = _generate_patients(rng, n_patients, start)
    encounters = _generate_encounters(rng, patients, start)
    users = _generate_users(rng, n_users)
    relationships = _generate_relationships(rng, users, encounters)
    notes = _generate_notes(rng, encounters)
    events = _generate_events(
        rng=rng,
        n_events=n_events,
        suspicious_rate=suspicious_rate,
        users=users,
        patients=patients,
        encounters=encounters,
        relationships=relationships,
    )

    tables = {
        "patients": patients,
        "encounters": encounters,
        "users": users,
        "relationships": relationships,
        "notes": notes,
        "events": events,
    }

    if write_csv:
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            frame.to_csv(output_dir / f"{name}.csv", index=False)

    return tables


def load_benchmark(input_dir: str | Path = DEFAULT_OUTPUT_DIR) -> dict[str, pd.DataFrame]:
    input_dir = Path(input_dir)
    return {
        name: pd.read_csv(input_dir / f"{name}.csv")
        for name in ["patients", "encounters", "users", "relationships", "notes", "events"]
    }


def _generate_patients(rng: np.random.Generator, n_patients: int, start: pd.Timestamp) -> pd.DataFrame:
    patient_ids = [f"P{idx:05d}" for idx in range(1, n_patients + 1)]
    diagnoses = rng.choice(DIAGNOSES, size=n_patients, p=[0.22, 0.18, 0.16, 0.18, 0.14, 0.12])
    departments = [_department_for_diagnosis(diagnosis) for diagnosis in diagnoses]
    admit_offsets = rng.integers(0, 45 * 24, size=n_patients)
    lengths = rng.integers(1, 12 * 24, size=n_patients)
    admit_times = [start + pd.Timedelta(hours=int(offset)) for offset in admit_offsets]
    discharge_times = [admit + pd.Timedelta(hours=int(length)) for admit, length in zip(admit_times, lengths)]

    return pd.DataFrame(
        {
            "patient_id": patient_ids,
            "age": rng.integers(18, 91, size=n_patients),
            "gender": rng.choice(["F", "M", "X"], size=n_patients, p=[0.50, 0.48, 0.02]),
            "diagnosis": diagnoses,
            "outcome": rng.choice(OUTCOMES, size=n_patients, p=[0.52, 0.24, 0.17, 0.07]),
            "department": departments,
            "admit_time": admit_times,
            "discharge_time": discharge_times,
            "high_interest_patient": rng.random(n_patients) < 0.035,
        }
    )


def _generate_encounters(
    rng: np.random.Generator,
    patients: pd.DataFrame,
    start: pd.Timestamp,
) -> pd.DataFrame:
    encounters = patients[
        ["patient_id", "department", "admit_time", "discharge_time"]
    ].copy()
    encounters.insert(0, "encounter_id", [f"E{idx:05d}" for idx in range(1, len(encounters) + 1)])
    encounters["encounter_type"] = rng.choice(
        ["ED", "inpatient", "outpatient", "consult"],
        size=len(encounters),
        p=[0.22, 0.40, 0.25, 0.13],
    )
    return encounters


def _generate_users(rng: np.random.Generator, n_users: int) -> pd.DataFrame:
    roles = rng.choice(ROLES, size=n_users, p=[0.28, 0.25, 0.14, 0.11, 0.12, 0.10])
    departments = []
    for role in roles:
        if role == "researcher":
            departments.append("research")
        elif role == "billing":
            departments.append("billing")
        elif role == "compliance":
            departments.append("billing")
        else:
            departments.append(rng.choice(DEPARTMENTS[:5]))

    return pd.DataFrame(
        {
            "user_id": [f"U{idx:04d}" for idx in range(1, n_users + 1)],
            "role": roles,
            "department": departments,
            "shift_start_hour": rng.choice([6, 7, 8, 18, 19], size=n_users, p=[0.18, 0.22, 0.36, 0.14, 0.10]),
            "shift_length_hours": rng.choice([8, 10, 12], size=n_users, p=[0.56, 0.20, 0.24]),
        }
    )


def _generate_relationships(
    rng: np.random.Generator,
    users: pd.DataFrame,
    encounters: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    clinical_users = users[users["role"].isin(["doctor", "nurse", "pharmacist"])]

    for _, encounter in encounters.iterrows():
        department_users = clinical_users[clinical_users["department"] == encounter["department"]]
        if department_users.empty:
            department_users = clinical_users

        team_size = int(rng.integers(2, 5))
        assigned = department_users.sample(n=min(team_size, len(department_users)), random_state=int(rng.integers(0, 1_000_000)))
        for _, user in assigned.iterrows():
            rows.append(
                {
                    "user_id": user["user_id"],
                    "patient_id": encounter["patient_id"],
                    "encounter_id": encounter["encounter_id"],
                    "relationship_type": "care_team",
                    "start_time": encounter["admit_time"],
                    "end_time": encounter["discharge_time"],
                }
            )

        if rng.random() < 0.22:
            specialist = clinical_users.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
            rows.append(
                {
                    "user_id": specialist["user_id"],
                    "patient_id": encounter["patient_id"],
                    "encounter_id": encounter["encounter_id"],
                    "relationship_type": "consult",
                    "start_time": encounter["admit_time"] + pd.Timedelta(hours=2),
                    "end_time": encounter["discharge_time"],
                }
            )

    return pd.DataFrame(rows)


def _generate_notes(rng: np.random.Generator, encounters: pd.DataFrame) -> pd.DataFrame:
    rows = []
    note_id = 1
    for _, encounter in encounters.iterrows():
        for note_type in rng.choice(NOTE_TYPES, size=int(rng.integers(1, 4)), replace=False):
            sensitive_keyword = rng.choice(SENSITIVE_KEYWORDS) if note_type in {"psychiatry", "social", "genetics"} else ""
            rows.append(
                {
                    "note_id": f"N{note_id:06d}",
                    "patient_id": encounter["patient_id"],
                    "encounter_id": encounter["encounter_id"],
                    "note_type": note_type,
                    "sensitive_keyword": sensitive_keyword,
                    "note_text": _note_text(note_type, sensitive_keyword),
                }
            )
            note_id += 1
    return pd.DataFrame(rows)


def _generate_events(
    rng: np.random.Generator,
    n_events: int,
    suspicious_rate: float,
    users: pd.DataFrame,
    patients: pd.DataFrame,
    encounters: pd.DataFrame,
    relationships: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    relationship_lookup = relationships.merge(users, on="user_id", suffixes=("", "_user"))
    encounter_lookup = encounters.merge(
        patients[["patient_id", "diagnosis", "outcome", "high_interest_patient"]],
        on="patient_id",
        how="left",
    )

    suspicious_scenarios = [scenario for scenario in SCENARIOS if scenario != "normal_workflow"]
    for idx in range(1, n_events + 1):
        is_suspicious = rng.random() < suspicious_rate
        scenario = rng.choice(suspicious_scenarios) if is_suspicious else "normal_workflow"

        if scenario == "normal_workflow" or (not is_suspicious and not relationship_lookup.empty):
            event = _normal_event(rng, relationship_lookup, encounter_lookup)
        else:
            event = _suspicious_event(rng, scenario, users, encounter_lookup)

        event["event_id"] = f"A{idx:07d}"
        event["scenario"] = scenario
        event["label"] = int(scenario != "normal_workflow")
        event["risk_tier"] = _risk_tier_for_scenario(scenario)
        rows.append(event)

    events = pd.DataFrame(rows)
    ordered_columns = [
        "event_id",
        "timestamp",
        "user_id",
        "role",
        "user_department",
        "patient_id",
        "encounter_id",
        "patient_department",
        "diagnosis",
        "outcome",
        "query_type",
        "note_type",
        "keyword",
        "result_count",
        "relationship_match",
        "scenario",
        "risk_tier",
        "label",
    ]
    return events[ordered_columns].sort_values("timestamp").reset_index(drop=True)


def _normal_event(
    rng: np.random.Generator,
    relationship_lookup: pd.DataFrame,
    encounter_lookup: pd.DataFrame,
) -> dict:
    relation = relationship_lookup.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
    encounter = encounter_lookup[encounter_lookup["encounter_id"] == relation["encounter_id"]].iloc[0]
    start = pd.Timestamp(relation["start_time"])
    end = pd.Timestamp(relation["end_time"])
    if end <= start:
        end = start + pd.Timedelta(hours=8)
    timestamp = start + pd.Timedelta(minutes=int(rng.integers(0, max(1, int((end - start).total_seconds() / 60)))))
    timestamp = _nudge_to_shift(timestamp, int(relation["shift_start_hour"]), int(relation["shift_length_hours"]), rng)

    event = {
        "timestamp": timestamp,
        "user_id": relation["user_id"],
        "role": relation["role"],
        "user_department": relation["department"],
        "patient_id": relation["patient_id"],
        "encounter_id": relation["encounter_id"],
        "patient_department": encounter["department"],
        "diagnosis": encounter["diagnosis"],
        "outcome": encounter["outcome"],
        "query_type": rng.choice(["chart_view", "note_view", "medication_review"], p=[0.48, 0.34, 0.18]),
        "note_type": rng.choice(["progress", "medication", "discharge"], p=[0.55, 0.30, 0.15]),
        "keyword": "",
        "result_count": int(rng.integers(8, 46)),
        "relationship_match": True,
    }

    # Legitimate care can still look odd: cross-cover, small cohorts, late shifts,
    # and non-sensitive keyword searches keep the benchmark from being trivial.
    if rng.random() < 0.12:
        event["relationship_match"] = False
    if rng.random() < 0.10:
        event["timestamp"] = pd.Timestamp(event["timestamp"]).normalize() + pd.Timedelta(
            hours=int(rng.choice([1, 2, 22, 23])),
            minutes=int(rng.integers(0, 60)),
        )
    if rng.random() < 0.08:
        event["result_count"] = int(rng.choice([2, 3, 4, 5]))
    if rng.random() < 0.08:
        event["query_type"] = "keyword_search"
        event["keyword"] = str(rng.choice(["epilepsy", "follow-up", "medication", "discharge"]))
    if rng.random() < 0.04:
        event["query_type"] = "keyword_search"
        event["keyword"] = str(rng.choice(["psychiatric", "pregnancy", "substance"]))
        event["note_type"] = str(rng.choice(["psychiatry", "social"]))
    if rng.random() < 0.06:
        event["user_department"] = str(rng.choice([dept for dept in DEPARTMENTS[:5] if dept != event["patient_department"]]))
    return event


def _suspicious_event(
    rng: np.random.Generator,
    scenario: str,
    users: pd.DataFrame,
    encounter_lookup: pd.DataFrame,
) -> dict:
    encounter = encounter_lookup.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
    if scenario == "high_interest_patient_curiosity":
        high_interest = encounter_lookup[encounter_lookup["high_interest_patient"]]
        if not high_interest.empty:
            encounter = high_interest.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]

    user = users.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
    if scenario in {"role_context_mismatch", "sensitive_keyword_search"}:
        candidates = users[users["role"].isin(["researcher", "billing"])]
        if not candidates.empty:
            user = candidates.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]

    admit = pd.Timestamp(encounter["admit_time"])
    discharge = pd.Timestamp(encounter["discharge_time"])
    timestamp = admit + pd.Timedelta(hours=int(rng.integers(1, 72)))
    relationship_match = bool(rng.random() < 0.24)
    result_count = int(rng.choice([1, 2, 3, 5, 8], p=[0.32, 0.24, 0.18, 0.16, 0.10]))
    keyword = ""
    query_type = "chart_view"
    note_type = rng.choice(NOTE_TYPES)

    if scenario == "cross_department_browsing":
        mismatched = users[users["department"] != encounter["department"]]
        if not mismatched.empty:
            user = mismatched.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
    elif scenario == "after_hours_repeated_access":
        timestamp = admit.normalize() + pd.Timedelta(days=int(rng.integers(0, 35)), hours=int(rng.choice([1, 2, 23])))
    elif scenario == "sensitive_keyword_search":
        keyword = str(rng.choice(SENSITIVE_KEYWORDS))
        query_type = "keyword_search"
        note_type = str(rng.choice(["psychiatry", "social", "genetics"]))
    elif scenario == "post_relationship_access":
        timestamp = discharge + pd.Timedelta(days=int(rng.integers(2, 18)), hours=int(rng.integers(0, 24)))
    elif scenario == "multi_patient_sweep":
        result_count = int(rng.integers(35, 150))
        query_type = "cohort_query"
    elif scenario == "high_interest_patient_curiosity":
        result_count = int(rng.choice([1, 2]))
    elif scenario == "role_context_mismatch":
        query_type = rng.choice(["note_view", "keyword_search"])
        keyword = str(rng.choice(["hippocampus", "psychiatric", "genetic"]))

    if rng.random() < 0.16:
        relationship_match = True
        result_count = int(rng.integers(8, 36))
        keyword = "" if rng.random() < 0.75 else keyword
        note_type = "progress" if rng.random() < 0.70 else note_type
        query_type = "chart_view" if rng.random() < 0.70 else query_type
        user_department = encounter["department"] if rng.random() < 0.80 else user["department"]
    else:
        user_department = user["department"]

    return {
        "timestamp": timestamp,
        "user_id": user["user_id"],
        "role": user["role"],
        "user_department": user_department,
        "patient_id": encounter["patient_id"],
        "encounter_id": encounter["encounter_id"],
        "patient_department": encounter["department"],
        "diagnosis": encounter["diagnosis"],
        "outcome": encounter["outcome"],
        "query_type": query_type,
        "note_type": note_type,
        "keyword": keyword,
        "result_count": result_count,
        "relationship_match": relationship_match,
    }


def _department_for_diagnosis(diagnosis: str) -> str:
    return {
        "epilepsy": "neurology",
        "stroke": "neurology",
        "heart failure": "cardiology",
        "diabetes": "ED",
        "depression": "psychiatry",
        "cancer": "oncology",
    }.get(diagnosis, "ED")


def _note_text(note_type: str, sensitive_keyword: str) -> str:
    if sensitive_keyword:
        return f"{note_type} note mentions {sensitive_keyword} context and follow-up."
    return f"{note_type} note with routine care details and follow-up."


def _nudge_to_shift(
    timestamp: pd.Timestamp,
    shift_start: int,
    shift_length: int,
    rng: np.random.Generator,
) -> pd.Timestamp:
    if rng.random() < 0.86:
        hour = int((shift_start + rng.integers(0, shift_length)) % 24)
        return timestamp.normalize() + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60)))
    return timestamp


def _risk_tier_for_scenario(scenario: str) -> str:
    if scenario == "normal_workflow":
        return "none"
    if scenario in {"sensitive_keyword_search", "post_relationship_access", "high_interest_patient_curiosity"}:
        return "high"
    if scenario in {"after_hours_repeated_access", "multi_patient_sweep", "role_context_mismatch"}:
        return "medium"
    return "low"


if __name__ == "__main__":
    generated = generate_benchmark()
    print(f"Generated {len(generated['events'])} access/query events in {DEFAULT_OUTPUT_DIR}")
