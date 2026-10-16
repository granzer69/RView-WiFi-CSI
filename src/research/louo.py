"""Aggregate LOUO classical experiment artifacts."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LOUO_ROOT = REPO_ROOT / "artifacts" / "louo"


def iter_louo_metrics(repo_root: Path | None = None) -> list[dict[str, Any]]:
    root = repo_root or REPO_ROOT
    louo_root = root / "artifacts" / "louo"
    if not louo_root.is_dir():
        return []

    entries: list[dict[str, Any]] = []
    for family_dir in sorted(louo_root.glob("louo_*")):
        family = family_dir.name.replace("louo_", "", 1)
        for run_dir in sorted(family_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            manifest_path = run_dir / "manifest.json"
            if manifest_path.is_file():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                run_id = manifest.get("run_id", run_dir.name)
            else:
                manifest = None
                run_id = run_dir.name

            for fold_dir in sorted(run_dir.glob("user_*")):
                metrics_path = fold_dir / "metrics.json"
                if not metrics_path.is_file():
                    continue
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                held_out = metrics.get("held_out_participant")
                if held_out is None:
                    held_out = int(fold_dir.name.split("_", 1)[1])
                test = metrics.get("test") or {}
                entries.append(
                    {
                        "family": family,
                        "run_id": run_id,
                        "held_out_participant": int(held_out),
                        "split_strategy": metrics.get("split_strategy"),
                        "artifact_dir": str(fold_dir.relative_to(root)),
                        "metrics_path": str(metrics_path.relative_to(root)),
                        "assignment_sha256": metrics.get("assignment_sha256"),
                        "counts": metrics.get("counts"),
                        "test_macro_f1": test.get("macro_f1"),
                        "test_accuracy": test.get("accuracy"),
                        "test": test,
                        "manifest_path": str(manifest_path.relative_to(root)) if manifest_path.is_file() else None,
                    }
                )
    return entries


def summarize_louo_macro_f1(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[float]] = {}
    for entry in entries:
        value = entry.get("test_macro_f1")
        if value is None:
            continue
        by_family.setdefault(entry["family"], []).append(float(value))

    summary: dict[str, Any] = {}
    for family, values in sorted(by_family.items()):
        summary[family] = {
            "fold_count": len(values),
            "mean_macro_f1": statistics.mean(values),
            "std_macro_f1": statistics.pstdev(values) if len(values) > 1 else 0.0,
            "min_macro_f1": min(values),
            "max_macro_f1": max(values),
            "per_fold": values,
        }
    return summary


def build_louo_export_payload(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    entries = iter_louo_metrics(root)
    return {
        "dataset_id": "esp-fi-har",
        "evaluation_protocol": "leave_one_user_out",
        "status": "complete" if entries else "pending",
        "integrity_note": (
            "LOUO metrics are separate from frozen v2 in_domain/cross_user/cross_environment baselines. "
            "Each fold holds out one participant entirely for test; val is one participant among the other seven."
        ),
        "folds": entries,
        "summary": summarize_louo_macro_f1(entries),
    }
