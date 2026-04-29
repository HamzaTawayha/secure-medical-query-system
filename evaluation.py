from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from baselines import CORE_BASELINE_MODES, score_feature_frame
from benchmark_generator import DEFAULT_OUTPUT_DIR, generate_benchmark, load_benchmark
from features import FEATURE_COLUMNS, zero_feature_group, build_event_features
from ml_model import train_logistic_model


DEFAULT_RESULTS_DIR = Path("results")


def run_evaluation(
    input_dir: str | Path = DEFAULT_OUTPUT_DIR,
    output_dir: str | Path = DEFAULT_RESULTS_DIR,
    seed: int = 42,
    generate_if_missing: bool = True,
) -> dict[str, pd.DataFrame]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if generate_if_missing and not (input_dir / "events.csv").exists():
        generate_benchmark(output_dir=input_dir, seed=seed)

    tables = load_benchmark(input_dir)
    feature_frame = build_event_features(
        tables["events"],
        patients=tables["patients"],
        encounters=tables["encounters"],
        users=tables["users"],
        relationships=tables["relationships"],
    )
    train_frame, test_frame = temporal_split(feature_frame)
    model_bundle = train_logistic_model(train_frame)

    event_scores = []
    metric_rows = []
    for mode in CORE_BASELINE_MODES:
        scored = score_feature_frame(test_frame, mode=mode, model_bundle=model_bundle)
        scored = scored.merge(test_frame[["event_id", "label", "scenario", "risk_tier"]], on="event_id", how="left")
        event_scores.append(scored)
        metric_rows.append({"mode": mode, **compute_metrics(scored["label"], scored["risk_score"])})

    ablation_rows = run_ablations(test_frame, model_bundle)
    baseline_results = pd.DataFrame(metric_rows)
    ablation_results = pd.DataFrame(ablation_rows)
    event_scores = pd.concat(event_scores, ignore_index=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_results.to_csv(output_dir / "baseline_results.csv", index=False)
    ablation_results.to_csv(output_dir / "ablation_results.csv", index=False)
    event_scores.to_csv(output_dir / "event_scores.csv", index=False)

    return {
        "baseline_results": baseline_results,
        "ablation_results": ablation_results,
        "event_scores": event_scores,
    }


def temporal_split(feature_frame: pd.DataFrame, train_fraction: float = 0.70) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = feature_frame.copy()
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.sort_values("timestamp")
    split_index = max(1, int(len(frame) * train_fraction))
    return frame.iloc[:split_index].reset_index(drop=True), frame.iloc[split_index:].reset_index(drop=True)


def compute_metrics(labels, scores, budgets=(0.01, 0.05, 0.10), target_recall=0.80) -> dict:
    from sklearn.metrics import average_precision_score, f1_score, roc_auc_score

    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    predictions = (scores >= 4.0).astype(int)

    metrics = {
        "pr_auc": _safe_metric(average_precision_score, labels, scores),
        "roc_auc": _safe_metric(roc_auc_score, labels, scores),
        "f1": _safe_metric(f1_score, labels, predictions),
    }

    for budget in budgets:
        precision, recall = precision_recall_at_budget(labels, scores, budget)
        label = int(budget * 100)
        metrics[f"precision_at_{label}pct"] = precision
        metrics[f"recall_at_{label}pct"] = recall

    metrics["workload_reduction_at_80_recall"] = workload_reduction_at_recall(labels, scores, target_recall)
    return metrics


def precision_recall_at_budget(labels, scores, budget: float) -> tuple[float, float]:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    if len(labels) == 0:
        return 0.0, 0.0

    k = max(1, int(np.ceil(len(labels) * budget)))
    order = np.argsort(-scores)
    selected = labels[order[:k]]
    positives = labels.sum()
    precision = float(selected.sum() / k)
    recall = float(selected.sum() / positives) if positives else 0.0
    return round(precision, 4), round(recall, 4)


def workload_reduction_at_recall(labels, scores, target_recall: float = 0.80) -> float:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    positives = labels.sum()
    if positives == 0:
        return 0.0

    order = np.argsort(-scores)
    cumulative = np.cumsum(labels[order])
    target_hits = target_recall * positives
    reached = np.where(cumulative >= target_hits)[0]
    if len(reached) == 0:
        return 0.0
    reviewed = reached[0] + 1
    return round(1.0 - (reviewed / len(labels)), 4)


def run_ablations(test_frame: pd.DataFrame, model_bundle: dict) -> list[dict]:
    rows = []
    ablations = {
        "hybrid_full": test_frame,
        "hybrid_without_temporal": zero_feature_group(test_frame, "temporal"),
        "hybrid_without_context": zero_feature_group(test_frame, "context"),
        "hybrid_without_text": zero_feature_group(test_frame, "text"),
    }
    for name, frame in ablations.items():
        scored = score_feature_frame(frame, mode="hybrid", model_bundle=model_bundle)
        rows.append({"ablation": name, **compute_metrics(test_frame["label"], scored["risk_score"])})

    ml_scored = score_feature_frame(test_frame, mode="ml_only", model_bundle=model_bundle)
    rows.append({"ablation": "hybrid_without_rule_layer", **compute_metrics(test_frame["label"], ml_scored["risk_score"])})
    return rows


def _safe_metric(metric_func, labels, scores_or_predictions):
    try:
        return round(float(metric_func(labels, scores_or_predictions)), 4)
    except ValueError:
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Run EHR access-risk triage benchmark evaluation.")
    parser.add_argument("--input-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_RESULTS_DIR))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    results = run_evaluation(input_dir=args.input_dir, output_dir=args.output_dir, seed=args.seed)
    print("Baseline results")
    print(results["baseline_results"].to_string(index=False))
    print()
    print("Ablation results")
    print(results["ablation_results"].to_string(index=False))


if __name__ == "__main__":
    main()
