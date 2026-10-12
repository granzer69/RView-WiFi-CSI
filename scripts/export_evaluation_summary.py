#!/usr/bin/env python3
"""Aggregate V2 metrics.json files into frontend evaluation summary JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
DEFAULT_OUT = REPO_ROOT / "frontend" / "public" / "evaluation" / "summary.json"
STRATEGIES = ("in_domain", "cross_user", "cross_environment")
BASELINE_FAMILIES = ("logreg", "rf", "cnn1d", "gru")
EXTENDED_FAMILIES = ("mlp", "gbdt", "tcn")

from research.generalization import BASELINE_RUN_IDS, EXTENDED_RUN_IDS


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _pinned_run_id(family: str) -> str | None:
    if family in BASELINE_RUN_IDS:
        return BASELINE_RUN_IDS[family]
    return EXTENDED_RUN_IDS.get(family)


def _latency_ms(metrics: dict) -> float | None:
    test = metrics.get("test") or {}
    latency = test.get("inference_latency") or metrics.get("inference_latency")
    if isinstance(latency, dict):
        return latency.get("mean_ms") or latency.get("p50_ms")
    if isinstance(latency, (int, float)):
        return float(latency)
    return None


def _model_size_bytes(metrics: dict) -> int | None:
    test = metrics.get("test") or {}
    size = test.get("model_size_bytes") or metrics.get("model_size_bytes")
    return int(size) if size is not None else None


DEEP_DEFAULT_CONFIG_FAMILIES = frozenset({"cnn1d", "gru", "tcn"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    models: list[dict] = []
    artifacts = REPO_ROOT / "artifacts"
    all_families = (*BASELINE_FAMILIES, *EXTENDED_FAMILIES)
    for family in all_families:
        run_id = _pinned_run_id(family)
        if not run_id:
            continue
        run_dir = artifacts / f"v2_{family}" / run_id
        if not run_dir.is_dir():
            continue
        for strategy in STRATEGIES:
            strategy_dir = run_dir / strategy
            metrics_path = strategy_dir / "metrics.json"
            if not metrics_path.is_file():
                continue
            metrics = json.loads(metrics_path.read_text())
            test = metrics.get("test") or {}
            per_class = test.get("per_class") or {}
            macro_precisions = [s.get("precision") for s in per_class.values() if s.get("precision") is not None]
            macro_recalls = [s.get("recall") for s in per_class.values() if s.get("recall") is not None]
            macro_precision = test.get("macro_precision")
            if macro_precision is None and macro_precisions:
                macro_precision = sum(macro_precisions) / len(macro_precisions)
            macro_recall = test.get("macro_recall")
            if macro_recall is None and macro_recalls:
                macro_recall = sum(macro_recalls) / len(macro_recalls)
            confusion = test.get("confusion_matrix")
            integrity_note = (
                "Measured on ESP-Fi holdout splits; labels inferred for "
                "scenarios 1/2/4 — not live hardware CSI."
            )
            if family in DEEP_DEFAULT_CONFIG_FAMILIES:
                integrity_note += (
                    " Default-config baseline (not hyperparameter-tuned)."
                )
            models.append(
                {
                    "model_id": f"v2_{family}_{strategy}_{run_dir.name}",
                    "family": family,
                    "split_strategy": strategy,
                    "run_id": run_dir.name,
                    "artifact_dir": str(strategy_dir.relative_to(REPO_ROOT)),
                    "macro_f1": test.get("macro_f1"),
                    "macro_precision": macro_precision,
                    "macro_recall": macro_recall,
                    "weighted_f1": test.get("weighted_f1"),
                    "accuracy": test.get("accuracy"),
                    "per_class": per_class,
                    "per_class_f1": {
                        name: stats.get("f1") for name, stats in per_class.items()
                    },
                    "per_class_precision": {
                        name: stats.get("precision") for name, stats in per_class.items()
                    },
                    "per_class_recall": {
                        name: stats.get("recall") for name, stats in per_class.items()
                    },
                    "confusion_matrix": confusion,
                    "latency_ms": _latency_ms(metrics),
                    "model_size_bytes": _model_size_bytes(metrics),
                    "integrity_note": integrity_note,
                    "config_baseline_note": (
                        "Default-config baseline (not hyperparameter-tuned)"
                        if family in DEEP_DEFAULT_CONFIG_FAMILIES
                        else None
                    ),
                }
            )

    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "dataset_id": "esp-fi-har",
        "generated_at": timestamp,
        "git_sha": _git_sha(),
        "baseline_run_ids": {**BASELINE_RUN_IDS, **EXTENDED_RUN_IDS},
        "generated_from": "artifacts/v2_*/<pinned_run_id>/<strategy>/metrics.json",
        "integrity_note": (
            "Offline evaluation on ESP-Fi. Dashboard replay uses the same dataset; "
            "presence is derived from model confidence, not hardware sensing."
        ),
        "models": models,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(models)} model/strategy rows)")


if __name__ == "__main__":
    main()
