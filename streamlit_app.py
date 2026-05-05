from pathlib import Path

import pandas as pd
import streamlit as st

from app_logic import run_secure_query
from baselines import SUPPORTED_DECISION_MODES
from evaluation import DEFAULT_RESULTS_DIR, run_evaluation


APP_TITLE = "EHR Access-Risk Triage"
RESULTS_DIR = Path(DEFAULT_RESULTS_DIR)
ROLE_OPTIONS = ["doctor", "nurse", "researcher", "pharmacist", "billing", "compliance"]
SCENARIOS = {
    "Custom": {
        "role": "researcher",
        "age_min": 30,
        "diagnosis": "",
        "outcome": "",
        "keyword": "",
    },
    "Low-risk doctor broad epilepsy query": {
        "role": "doctor",
        "age_min": 20,
        "diagnosis": "epilepsy",
        "outcome": "",
        "keyword": "",
    },
    "Medium-risk researcher poor outcome query": {
        "role": "researcher",
        "age_min": 30,
        "diagnosis": "epilepsy",
        "outcome": "poor",
        "keyword": "",
    },
    "High-risk researcher hippocampus isolation query": {
        "role": "researcher",
        "age_min": 30,
        "diagnosis": "epilepsy",
        "outcome": "",
        "keyword": "hippocampus",
    },
}


st.set_page_config(page_title=APP_TITLE, layout="wide")


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --border: #d7dee8;
            --muted: #5f6b7a;
            --ink: #1f2937;
            --surface: #ffffff;
            --soft: #f6f8fb;
            --accent: #0f766e;
            --warn: #b45309;
            --danger: #b91c1c;
        }

        .block-container {
            max-width: 1220px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .app-header {
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.25rem;
            padding-bottom: 1.25rem;
        }

        .app-kicker {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            margin: 0 0 0.35rem 0;
            text-transform: uppercase;
        }

        .app-header h1 {
            color: var(--ink);
            font-size: 2.2rem;
            font-weight: 760;
            letter-spacing: 0;
            margin: 0;
        }

        .app-subtitle {
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.55;
            margin: 0.45rem 0 0 0;
            max-width: 860px;
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.9rem 1rem;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-weight: 650;
        }

        div[data-testid="stMetricValue"] {
            color: var(--ink);
            font-size: 1.45rem;
            font-weight: 760;
        }

        .status-row {
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin: 0.25rem 0 0.75rem 0;
        }

        .status-pill {
            border-radius: 999px;
            display: inline-flex;
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0;
            padding: 0.32rem 0.72rem;
            text-transform: uppercase;
        }

        .status-allow {
            background: #e8f5f1;
            color: #0f766e;
        }

        .status-flag {
            background: #fff7ed;
            color: #b45309;
        }

        .status-block {
            background: #fef2f2;
            color: #b91c1c;
        }

        .status-neutral {
            background: #eef2f7;
            color: #44546a;
        }

        .meta-line {
            color: var(--muted);
            font-size: 0.92rem;
            margin: 0 0 0.7rem 0;
        }

        .section-rule {
            border-top: 1px solid var(--border);
            margin: 1.35rem 0 1rem 0;
        }

        .small-note {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.45;
        }

        .stButton > button {
            border-radius: 6px;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        """
        <div class="app-header">
            <p class="app-kicker">Clinical data security prototype</p>
            <h1>EHR Access-Risk Triage</h1>
            <p class="app-subtitle">
                Score access requests with RBAC, transparent rules, ML estimates,
                and hybrid ranking so compliance teams can review the highest-risk
                events first.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_score(value):
    return "n/a" if value is None else f"{float(value):.2f}"


def format_probability(value):
    return "n/a" if value is None else f"{float(value):.1%}"


def render_status_badges(result):
    decision = str(result.get("decision") or "UNKNOWN")
    priority = str(result.get("review_priority") or "none")
    decision_class = {
        "ALLOW": "status-allow",
        "FLAG": "status-flag",
        "BLOCK": "status-block",
    }.get(decision, "status-neutral")
    priority_class = "status-neutral" if priority in {"none", "low"} else "status-flag"
    st.markdown(
        f"""
        <div class="status-row">
            <span class="status-pill {decision_class}">{decision}</span>
            <span class="status-pill {priority_class}">Priority: {priority}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_message(decision):
    if decision == "BLOCK":
        st.error("Access denied because the query is too specific or too risky.")
    elif decision == "FLAG":
        st.warning("Access approved and prioritized for compliance review.")
    elif decision == "ALLOW":
        st.success("Access approved.")


def display_frame(records, empty_message):
    if records:
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


def existing_columns(frame, columns):
    return [column for column in columns if column in frame.columns]


inject_styles()
render_header()

if "query_result" not in st.session_state:
    st.session_state.query_result = None

query_tab, comparison_tab, queue_tab, summary_tab = st.tabs(
    ["Query Demo", "Baselines", "Review Queue", "Summary"]
)


with query_tab:
    st.subheader("Access Request")

    decision_mode_labels = {label: mode for mode, label in SUPPORTED_DECISION_MODES.items()}
    decision_labels = list(decision_mode_labels.keys())
    default_decision_label = "Hybrid triage" if "Hybrid triage" in decision_labels else "Rule-based baseline"

    control_col, scenario_col = st.columns([1, 2])
    with control_col:
        selected_decision_label = st.selectbox(
            "Decision system",
            decision_labels,
            index=decision_labels.index(default_decision_label),
        )
        decision_mode = decision_mode_labels[selected_decision_label]
        k_threshold = 3
        if decision_mode == "k_anonymity":
            k_threshold = st.number_input("k-anonymity threshold", min_value=2, max_value=20, value=3, step=1)

    with scenario_col:
        preset = st.selectbox("Demo scenario", list(SCENARIOS.keys()))

    defaults = SCENARIOS[preset]
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

    input_col1, input_col2 = st.columns(2)
    with input_col1:
        role = st.selectbox("User role", ROLE_OPTIONS, index=ROLE_OPTIONS.index(defaults["role"]))
        use_age_filter = st.checkbox("Use minimum age filter", value=True)
        age_min = (
            st.number_input("Minimum age", min_value=0, max_value=120, value=defaults["age_min"], step=1)
            if use_age_filter
            else None
        )
        diagnosis = st.text_input("Diagnosis", value=defaults["diagnosis"])

    with input_col2:
        outcome = st.text_input("Outcome", value=defaults["outcome"])
        keyword = st.text_input("Keyword in notes", value=defaults["keyword"])
        st.markdown('<p class="small-note">Blank filters are omitted from the submitted query.</p>', unsafe_allow_html=True)

    submitted = st.button("Run secure query", type="primary", use_container_width=True)
    if submitted:
        st.session_state.query_result = run_secure_query(
            role=role,
            age_min=age_min,
            diagnosis=diagnosis.strip() or None,
            outcome=outcome.strip() or None,
            keyword=keyword.strip() or None,
            decision_mode=decision_mode,
            k_threshold=k_threshold,
        )
        st.session_state.selected_decision_label = selected_decision_label

    result = st.session_state.query_result
    if result:
        st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
        st.subheader("Risk Analysis")
        render_status_badges(result)

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        metric_col1.metric("Risk score", format_score(result["risk_score"]))
        metric_col2.metric("Risk probability", format_probability(result["risk_probability"]))
        metric_col3.metric("Decision", result["decision"])
        metric_col4.metric("Review priority", result["review_priority"])

        decision_label = st.session_state.get("selected_decision_label", selected_decision_label)
        st.markdown(
            f'<p class="meta-line">Decision system: <strong>{decision_label}</strong> | Log ID: <strong>{result["log_id"]}</strong></p>',
            unsafe_allow_html=True,
        )

        if result.get("decision_reason"):
            st.write("**Decision reason:**", result["decision_reason"])
        render_decision_message(result.get("decision"))

        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.write("**Baseline scores**")
            st.json(result.get("baseline_scores") or {})
        with detail_col2:
            st.write("**Submitted query**")
            st.json(result["query_input"])

        if result.get("reason_codes"):
            st.write("**Reason codes**")
            st.dataframe(pd.DataFrame(result["reason_codes"]), use_container_width=True, hide_index=True)

        st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
        st.subheader("Structured Results")
        display_frame(result["patients"], "No patient records returned.")

        st.subheader("Unstructured Results")
        display_frame(result["notes"], "No note records returned.")


with comparison_tab:
    st.subheader("Baseline Results")
    if st.button("Run local benchmark evaluation"):
        with st.spinner("Running benchmark evaluation"):
            try:
                run_evaluation()
                st.success("Evaluation complete.")
            except Exception as exc:
                st.error(f"Evaluation failed: {exc}")

    baseline_path = RESULTS_DIR / "baseline_results.csv"
    if baseline_path.exists():
        baseline_results = pd.read_csv(baseline_path)
        key_columns = ["mode", "pr_auc", "precision_at_5pct", "recall_at_5pct", "workload_reduction_at_80_recall"]
        st.dataframe(baseline_results[existing_columns(baseline_results, key_columns)], use_container_width=True, hide_index=True)

        chart_columns = existing_columns(baseline_results, ["pr_auc", "precision_at_5pct", "recall_at_5pct"])
        if chart_columns:
            chart_frame = baseline_results.set_index("mode")[chart_columns]
            st.bar_chart(chart_frame)
    else:
        st.info("No baseline results found. Run the benchmark evaluation to populate this view.")


with queue_tab:
    st.subheader("Reviewer Queue")
    event_scores_path = RESULTS_DIR / "event_scores.csv"
    if event_scores_path.exists():
        event_scores = pd.read_csv(event_scores_path)
        hybrid_scores = event_scores[event_scores["mode"] == "hybrid"].copy()
        hybrid_scores = hybrid_scores.sort_values(["risk_score", "risk_probability"], ascending=False)
        visible_columns = existing_columns(
            hybrid_scores,
            [
                "event_id",
                "risk_score",
                "risk_probability",
                "decision",
                "review_priority",
                "scenario",
                "risk_tier",
                "reason_codes",
            ],
        )
        st.dataframe(hybrid_scores[visible_columns].head(100), use_container_width=True, hide_index=True)
    else:
        st.info("No reviewer queue found. Run the benchmark evaluation to populate this view.")


with summary_tab:
    st.subheader("Benchmark Summary")
    ablation_path = RESULTS_DIR / "ablation_results.csv"
    if ablation_path.exists():
        st.write("**Ablation results**")
        st.dataframe(pd.read_csv(ablation_path), use_container_width=True, hide_index=True)
    else:
        st.info("No ablation results found. Run the benchmark evaluation to populate this view.")

    st.write("**Output paths**")
    st.json(
        {
            "benchmark_data": str(Path("data") / "benchmark"),
            "model_artifacts": str(Path("artifacts")),
            "evaluation_results": str(RESULTS_DIR),
        }
    )
