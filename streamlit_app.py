import streamlit as st
from app_logic import run_secure_query

st.set_page_config(page_title="Secure Medical Query System", layout="wide")

st.title("Secure Medical Query System")
st.write("Hybrid Azure SQL + MongoDB query interface with role-aware risk analysis")

st.markdown("---")

st.subheader("Preset Demo Queries")

preset = st.selectbox(
    "Choose a demo scenario",
    [
        "Custom",
        "Low-risk doctor broad epilepsy query",
        "Medium-risk researcher poor outcome query",
        "High-risk researcher hippocampus isolation query"
    ]
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
    default_outcome = ""
    default_keyword = ""
elif preset == "Medium-risk researcher poor outcome query":
    default_role = "researcher"
    default_age = 30
    default_diagnosis = "epilepsy"
    default_outcome = "poor"
    default_keyword = ""
elif preset == "High-risk researcher hippocampus isolation query":
    default_role = "researcher"
    default_age = 30
    default_diagnosis = "epilepsy"
    default_outcome = ""
    default_keyword = "hippocampus"

st.markdown("---")

st.subheader("Query Inputs")

col1, col2 = st.columns(2)

with col1:
    role = st.selectbox("User Role", ["doctor", "researcher"], index=0 if default_role == "doctor" else 1)

    use_age_filter = st.checkbox("Use minimum age filter", value=True)
    if use_age_filter:
        age_min = st.number_input("Minimum Age", min_value=0, max_value=120, value=default_age, step=1)
    else:
        age_min = None

    diagnosis = st.text_input("Diagnosis", value=default_diagnosis)

with col2:
    outcome = st.text_input("Outcome (optional)", value=default_outcome)
    keyword = st.text_input("Keyword in Notes (optional)", value=default_keyword)

run_button = st.button("Run Secure Query")

if run_button:
    if diagnosis.strip() == "":
        diagnosis = None

    if outcome.strip() == "":
        outcome = None

    if keyword.strip() == "":
        keyword = None

    result = run_secure_query(
        role=role,
        age_min=age_min,
        diagnosis=diagnosis,
        outcome=outcome,
        keyword=keyword
    )

    st.markdown("---")
    st.subheader("Risk Analysis")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Risk Score", result["risk_score"])
    metric_col2.metric("Decision", result["decision"])
    metric_col3.metric("Log ID", result["log_id"])

    st.write("**Submitted Query Input:**")
    st.json(result["query_input"])

    if result["decision"] == "BLOCK":
        st.error("Access denied: query is too specific and may expose sensitive patient data.")
    elif result["decision"] == "FLAG":
        st.warning("Caution: query is moderately sensitive and logged for review.")
    else:
        st.success("Query approved.")

    st.markdown("---")
    st.subheader("Structured Results (Azure SQL)")

    if result["patients"]:
        st.dataframe(result["patients"], use_container_width=True)
    else:
        st.write("No patient records returned.")

    st.markdown("---")
    st.subheader("Unstructured Results (MongoDB Notes)")

    if result["notes"]:
        st.dataframe(result["notes"], use_container_width=True)
    else:
        st.write("No note records returned.")