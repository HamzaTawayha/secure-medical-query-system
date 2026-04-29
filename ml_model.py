from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from features import FEATURE_COLUMNS


ARTIFACT_DIR = Path("artifacts")
MODEL_PATH = ARTIFACT_DIR / "logistic_risk_model.joblib"
ISOLATION_FOREST_PATH = ARTIFACT_DIR / "isolation_forest_model.joblib"


def train_logistic_model(
    feature_frame: pd.DataFrame,
    label_col: str = "label",
    model_path: str | Path = MODEL_PATH,
) -> dict:
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    train_frame = _ensure_feature_columns(feature_frame)
    labels = train_frame[label_col].astype(int)

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        ]
    )
    pipeline.fit(train_frame[FEATURE_COLUMNS], labels)

    bundle = {
        "model_type": "logistic_regression",
        "model": pipeline,
        "feature_columns": FEATURE_COLUMNS,
    }
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    return bundle


def train_isolation_forest(
    feature_frame: pd.DataFrame,
    model_path: str | Path = ISOLATION_FOREST_PATH,
) -> dict:
    from sklearn.ensemble import IsolationForest

    train_frame = _ensure_feature_columns(feature_frame)
    model = IsolationForest(n_estimators=200, contamination=0.12, random_state=42)
    model.fit(train_frame[FEATURE_COLUMNS])
    bundle = {
        "model_type": "isolation_forest",
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
    }
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    return bundle


def load_model(model_path: str | Path = MODEL_PATH) -> dict | None:
    model_path = Path(model_path)
    if not model_path.exists():
        return None
    return joblib.load(model_path)


def predict_probability(feature_frame: pd.DataFrame, model_bundle: dict | None = None) -> np.ndarray:
    frame = _ensure_feature_columns(feature_frame)
    if model_bundle is None:
        model_bundle = load_model()

    if model_bundle is None:
        return fallback_probability(frame)

    model_type = model_bundle.get("model_type")
    model = model_bundle["model"]
    columns = model_bundle.get("feature_columns", FEATURE_COLUMNS)

    if model_type == "isolation_forest":
        raw_scores = -model.decision_function(frame[columns])
        return _minmax(raw_scores)

    if hasattr(model, "predict_proba"):
        return model.predict_proba(frame[columns])[:, 1]

    return fallback_probability(frame)


def fallback_probability(feature_frame: pd.DataFrame) -> np.ndarray:
    frame = _ensure_feature_columns(feature_frame)
    weighted = (
        1.6 * frame["no_relationship"]
        + 1.1 * frame["after_hours"]
        + 1.0 * frame["outside_shift"]
        + 1.7 * frame["single_patient_result"]
        + 1.0 * frame["small_result_count"]
        + 1.1 * frame["keyword_present"]
        + 1.8 * frame["sensitive_keyword_flag"]
        + 1.2 * frame["note_type_sensitive"]
        + 1.0 * frame["cross_department_access"]
        + 1.5 * frame["post_discharge_access"]
        + 1.2 * frame["high_interest_patient"]
        + 0.18 * frame["recent_user_event_count_1h"]
        + 0.16 * frame["recent_user_patient_count_1h"]
        + 0.7 * frame["query_type_keyword_search"]
        + 0.5 * frame["query_type_cohort_query"]
        + 0.8 * frame["is_researcher"]
        + 0.6 * frame["is_billing"]
        - 1.2 * frame["relationship_match"]
        - 0.5 * frame["is_clinical_role"]
    )
    probabilities = 1 / (1 + np.exp(-(weighted - 2.0)))
    return np.clip(probabilities, 0.0, 1.0).to_numpy()


def _ensure_feature_columns(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in FEATURE_COLUMNS:
        if column not in output.columns:
            output[column] = 0
    output[FEATURE_COLUMNS] = output[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0)
    return output


def _minmax(values) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return values
    low = values.min()
    high = values.max()
    if high == low:
        return np.full_like(values, 0.5, dtype=float)
    return (values - low) / (high - low)
