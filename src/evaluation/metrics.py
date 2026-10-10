"""Classification metrics and latency measurement."""

from __future__ import annotations

import time
from typing import Any, Callable

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from ingestion.ml_contract import NORMALIZED_LABELS


def classification_report_dict(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    labels: tuple[str, ...] = NORMALIZED_LABELS,
) -> dict[str, Any]:
    label_ids = list(range(len(labels)))
    report = classification_report(
        y_true,
        y_pred,
        labels=label_ids,
        target_names=list(labels),
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=label_ids)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "per_class": {
            name: {
                "precision": float(report[name]["precision"]),
                "recall": float(report[name]["recall"]),
                "f1": float(report[name]["f1-score"]),
                "support": int(report[name]["support"]),
            }
            for name in labels
        },
        "confusion_matrix": {
            "labels": list(labels),
            "matrix": cm.tolist(),
        },
    }


def measure_inference_latency_ms(
    predict_fn: Callable[[np.ndarray], np.ndarray],
    features: np.ndarray,
    *,
    warmup: int = 3,
    repeats: int = 20,
) -> dict[str, float]:
    """Return per-sample latency statistics in milliseconds."""
    batch = np.asarray(features, dtype=np.float64)
    if batch.ndim != 2 or batch.shape[0] < 1:
        raise ValueError("features must be a non-empty 2D array")
    for _ in range(warmup):
        predict_fn(batch[:1])
    timings: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        predict_fn(batch)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        timings.append(elapsed_ms / batch.shape[0])
    ordered = sorted(timings)
    return {
        "per_sample_ms_mean": float(np.mean(timings)),
        "per_sample_ms_median": float(ordered[len(ordered) // 2]),
        "per_sample_ms_p95": float(ordered[int(0.95 * (len(ordered) - 1))]),
    }
