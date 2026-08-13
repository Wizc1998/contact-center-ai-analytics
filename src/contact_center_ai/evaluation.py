"""Evaluation utilities that make model quality measurable and comparable."""

from __future__ import annotations

import json
from pathlib import Path

from .baseline import BaselineAnalyzer
from .models import Analyzer
from .redact import redact_pii


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate_topics(path: Path, analyzer: Analyzer | None = None) -> dict[str, object]:
    analyzer = analyzer or BaselineAnalyzer()
    truth: list[str] = []
    predictions: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            truth.append(row["expected_topic"])
            predictions.append(analyzer.analyze(redact_pii(row["text"]).text).topic)

    labels = sorted(set(truth) | set(predictions))
    per_class: dict[str, dict[str, float | int]] = {}
    for label in labels:
        tp = sum(actual == label and predicted == label for actual, predicted in zip(truth, predictions))
        fp = sum(actual != label and predicted == label for actual, predicted in zip(truth, predictions))
        fn = sum(actual == label and predicted != label for actual, predicted in zip(truth, predictions))
        precision = _safe_divide(tp, tp + fp)
        recall = _safe_divide(tp, tp + fn)
        f1 = _safe_divide(2 * precision * recall, precision + recall)
        per_class[label] = {
            "support": truth.count(label),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    accuracy = _safe_divide(sum(a == p for a, p in zip(truth, predictions)), len(truth))
    macro_f1 = _safe_divide(sum(float(metrics["f1"]) for metrics in per_class.values()), len(labels))
    return {
        "records": len(truth),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
    }
