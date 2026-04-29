from pathlib import Path

import pandas as pd
import streamlit as st

from app_logic import run_secure_query
from baselines import SUPPORTED_DECISION_MODES
from evaluation import DEFAULT_RESULTS_DIR, run_evaluation


st.set_page_config(page_title="EHR Access-Risk Triage", layout="wide")

RESULTS_DIR = Path(DEFAULT_RESULTS_DIR)

st.title("EHR Access-Risk Triage")

query_tab, comparison_tab, queue_tab, summary_tab = st.tabs(
    ["Secure query demo", "Baseline comparison", "Reviewer queue", "Benchmark summary"]
)


with query_tab:
    st.subheader("Preset Demo Queries")

    decision_mode_labels = {
        label: mode for mode, label in SUPPORTED_DECISION_MODES.items()
    }
    decision_labels = list(decision_mode_labels.keys())
    default_decision_label = "Hybrid triage" if "Hybrid triage" in decision_labels else "Rule-based baseline"
    selected_decision_label = st.selectbox(
        "Decision system",
        decision_labels,
        index=decision_labels.index(default_decision_label),
    )
    decision_mode = decision_mode_labels[selected_decision_label]

    k_threshold = 3
    if decision_mode == "k_anonymity":
        k_threshold = st.number_input("k-anonymity threshold", min_value=2, max_value=20, value=3, step=1)

    preset = st.selectbox(
        "Choose a demo scenario",
        [
            "Custom",
            "Low-risk doctor broad epilepsy query",
            "Medium-risk researcher poor outcome query",
            "High-risk researcher hippocampus isolation query",
        ],
    )

    default_role = "researcher"
    default_age = 30
    default_diagnosis = ""
    default_outcome = ""
    default_keyword = ""

    if preset == "Low-risk doctor broad epilepsy query":
        default_role = "doctor"
        default_age = 20
        default_diagnosis = "epilepsy"
    elif preset == "Medium-risk researcher poor outcome query":
        default_role = "researcher"
        default_age = 30
        default_diagnosis = "epilepsy"
        default_outcome = "poor"
    elif preset == "High-risk researcher hippocampus isolation query":
        default_role = "researcher"
        default_age = 30
        default_diagnosis = "epilepsy"
        default_keyword = "hippocampus"

    st.markdown("---")
    st.subheader("Query Inputs")

    col1, col2 = st.columns(2)
    with col1:
        role = st.selectbox(
            "User Role",
            ["doctor", "nurse", "researcher", "pharmacist", "billing", "compliance"],
            index=["doctor", "nurse", "researcher", "pharmacist", "billing", "compliance"].index(default_role),
        )
        use_age_filter = st.checkbox("Use minimum age filter", value=True)
        age_min = st.number_input("Minimum Age", min_value=0, max_value=120, value=default_age, step=1) if use_age_filter else None
        diagnosis = st.text_input("Diagnosis", value=default_diagnosis)

    with col2:
        outcome = st.text_input("Outcome", value=default_outcome)
        keyword = st.text_input("Keyword in Notes", value=default_keyword)

    if st.button("Run Secure Query", type="primary"):
        diagnosis = diagnosis.strip() or None
        outcome = outcome.strip() or None
        keyword = keyword.strip() or None

        result = run_secure_query(
            role=role,
            age_min=age_min,
            diagnosis=diagnosis,
            outcome=outcome,
            keyword=keyword,
            decision_mode=decision_mode,
            k_threshold=k_threshold,
        )

        st.markdown("---")
        st.subheader("Risk Analysis")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        metric_col1.metric("Risk Score", result["risk_score"])
        metric_col2.metric("Risk Probability", result["risk_probability"])
        metric_col3.metric("Decision", result["decision"])
        metric_col4.metric("Review Priority", result["review_priority"])

        st.write("**Decision System:**", selected_decision_label)
        st.write("**Log ID:**", result["log_id"])
        if result.get("decision_reason"):
            st.write("**Decision Reason:**", result["decision_reason"])

        if result.get("baseline_scores"):
            st.write("**Baseline Scores:**")
            st.json(result["baseline_scores"])

        if result.get("reason_codes"):
            st.write("**Reason Codes:**")
            st.dataframe(pd.DataFrame(result["reason_codes"]), use_container_width=True, hide_index=True)

        st.write("**Submitted Query Input:**")
        st.json(result["query_input"])

        if result["decision"] == "BLOCK":
            st.error("Access denied: query is too specific or too risky.")
        elif result["decision"] == "FLAG":
            st.warning("Query approved and prioritized for review.")
        else:
            st.success("Query approved.")

        st.markdown("---")
        st.subheader("Structured Results")
        st.dataframe(result["patients"], use_container_width=True) if result["patients"] else st.write("No patient records returned.")

        st.markdown("---")
        st.subheader("Unstructured Results")
        st.dataframe(result["notes"], use_container_width=True) if result["notes"] else st.write("No note records returned.")


with comparison_tab:
    st.subheader("Baseline Results")
    if st.button("Run Local Benchmark Evaluation"):
        with st.spinner("Running benchmark evaluation"):
            try:
                run_evaluation()
                st.success("Evaluation complete.")
            except Exception as exc:
                st.error(f"Evaluation failed: {exc}")

    baseline_path = RESULTS_DIR / "baseline_results.csv"
    if baseline_path.exists():
        baseline_results = pd.read_csv(baseline_path)
        st.dataframe(baseline_results, use_container_width=True, hide_index=True)
        chart_frame = baseline_results.set_index("mode")[["pr_auc", "precision_at_5pct", "recall_at_5pct"]]
        st.bar_chart(chart_frame)
    else:
        st.info("No baseline results found.")


with queue_tab:
    st.subheader("Reviewer Queue")
    event_scores_path = RESULTS_DIR / "event_scores.csv"
    if event_scores_path.exists():
        event_scores = pd.read_csv(event_scores_path)
        hybrid_scores = event_scores[event_scores["mode"] == "hybrid"].copy()
        hybrid_scores = hybrid_scores.sort_values(["risk_score", "risk_probability"], ascending=False)
        visible_columns = [
            "event_id",
            "risk_score",
            "risk_probability",
            "decision",
            "review_priority",
            "scenario",
            "risk_tier",
            "reason_codes",
        ]
        st.dataframe(hybrid_scores[visible_columns].head(100), use_container_width=True, hide_index=True)
    else:
        st.info("No reviewer queue found.")


with summary_tab:
    st.subheader("Benchmark Summary")
    ablation_path = RESULTS_DIR / "ablation_results.csv"
    if ablation_path.exists():
        st.write("**Ablation Results:**")
        st.dataframe(pd.read_csv(ablation_path), use_container_width=True, hide_index=True)
    else:
        st.info("No ablation results found.")

    st.write("**Output Paths:**")
    st.json(
        {
            "benchmark_data": str(Path("data") / "benchmark"),
            "model_artifacts": str(Path("artifacts")),
            "evaluation_results": str(RESULTS_DIR),
        }
    )
