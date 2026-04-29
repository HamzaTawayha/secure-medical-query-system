from evaluation import compute_metrics, precision_recall_at_budget, workload_reduction_at_recall


def test_precision_recall_at_budget_uses_top_ranked_events():
    labels = [1, 0, 1, 0]
    scores = [0.9, 0.8, 0.7, 0.1]

    precision, recall = precision_recall_at_budget(labels, scores, budget=0.5)

    assert precision == 0.5
    assert recall == 0.5


def test_workload_reduction_and_metric_keys():
    labels = [1, 0, 1, 0, 1]
    scores = [0.9, 0.2, 0.8, 0.1, 0.7]

    reduction = workload_reduction_at_recall(labels, scores, target_recall=0.8)
    metrics = compute_metrics(labels, scores)

    assert reduction == 0.4
    assert "pr_auc" in metrics
    assert "precision_at_5pct" in metrics
    assert metrics["recall_at_10pct"] > 0
