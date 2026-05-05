# EHR Access-Risk Triage

A reproducible prototype for ranking potentially risky electronic health record
(EHR) access and query events. The project combines role-based policy checks,
rule-based risk scoring, lightweight machine learning, synthetic benchmark
generation, and a Streamlit reviewer dashboard.

The goal is not to replace clinical access controls. It is to prioritize events
for compliance review under limited audit capacity, while preserving clear reason
codes for each decision.

## What This Project Includes

- Hybrid access-risk scoring across RBAC, rule-based, ML-only, and combined modes.
- Deterministic synthetic benchmark generation for EHR access/query events.
- Budget-aware evaluation metrics such as precision@k, recall@k, PR-AUC, and
  workload reduction.
- Streamlit dashboard for demo queries, baseline comparison, reviewer queue
  inspection, and benchmark summaries.
- Azure SQL and MongoDB/Cosmos DB integration points for structured records,
  clinical notes, and query logs.

## Repository Layout

```text
.
|-- app_logic.py              # Query orchestration, scoring, logging, and response shaping
|-- baselines.py              # RBAC, k-anonymity, rules, ML-only, and hybrid scoring modes
|-- benchmark_generator.py    # Synthetic patients, encounters, users, notes, and access events
|-- db_cosmos.py              # MongoDB/Cosmos DB note search and audit-log writes
|-- db_sql.py                 # Azure SQL patient query helpers
|-- evaluation.py             # Benchmark evaluation, ranking metrics, and ablations
|-- features.py               # Feature extraction for live and benchmark events
|-- ml_model.py               # Logistic and isolation forest model utilities
|-- risk_engine.py            # Rule weights, reason codes, and decision thresholds
|-- streamlit_app.py          # Interactive reviewer-facing dashboard
|-- tests/                    # Unit tests for core scoring, features, and evaluation logic
`-- docs/ARCHITECTURE.md      # System design and data-flow notes
```

## Quick Start

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy the environment template and fill in your local database settings:

```powershell
Copy-Item .env.example .env
```

Generate the synthetic benchmark and evaluation outputs:

```powershell
python benchmark_generator.py
python -m evaluation
```

Run the Streamlit dashboard:

```powershell
streamlit run streamlit_app.py
```

Run the tests:

```powershell
python -m pytest
```

## Environment Variables

The live query path expects the following values in `.env`:

```text
SQL_SERVER=
SQL_DATABASE=
SQL_USERNAME=
SQL_PASSWORD=
MONGO_URI=
MONGO_DATABASE=
MONGO_COLLECTION_NOTES=
MONGO_COLLECTION_LOGS=
```

Generated benchmark data, trained model artifacts, and evaluation results are
ignored by Git so the repository stays lightweight.

## Evaluation Outputs

Running `python -m evaluation` writes:

- `results/baseline_results.csv`
- `results/ablation_results.csv`
- `results/event_scores.csv`

The Streamlit dashboard reads these files to populate the baseline comparison,
reviewer queue, and summary tabs.

## Privacy And Safety Notes

This repository is designed around synthetic benchmark data and demo database
connections. Do not commit real patient data, credentials, production logs, or
protected health information. Keep secrets in `.env` or your deployment secret
manager, not in source control.
