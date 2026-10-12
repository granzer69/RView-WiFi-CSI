"""Generalization metrics from baseline V2 artifacts only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGIES = ("in_domain", "cross_user", "cross_environment")
FAMILIES = ("logreg", "rf", "cnn1d", "gru")
EXTENDED_FAMILIES = ("mlp", "gbdt", "tcn")

BASELINE_RUN_IDS: dict[str, str] = {
    "logreg": "20261010T045500Z",
    "rf": "20261010T060000Z",
    "cnn1d": "20261010T070000Z",
    "gru": "20261010T080000Z",
}

# Pin extended-family runs after training (same protocol as baselines). When empty,
# extended_metrics_entries() uses the newest complete run under artifacts/v2_<family>/.
EXTENDED_RUN_IDS: dict[str, str] = {
    "mlp": "20261012T140000Z",
    "gbdt": "20261012T140000Z",
    "tcn": "20261012T140000Z",
}


@dataclass(frozen=True)
class BaselineMetricsRef:
    family: str
    run_id: str
    strategy: str
    metrics_path: Path
    artifact_dir: Path


def baseline_artifact_dir(repo_root: Path, family: str, run_id: str, strategy: str) -> Path:
    return repo_root / "artifacts" / f"v2_{family}" / run_id / strategy


def iter_baseline_metrics_refs(repo_root: Path | None = None) -> list[BaselineMetricsRef]:
    root = repo_root or REPO_ROOT
    refs: list[BaselineMetricsRef] = []
    for family in FAMILIES:
        run_id = BASELINE_RUN_IDS.get(family)
        if not run_id:
            continue
        for strategy in STRATEGIES:
            artifact_dir = baseline_artifact_dir(root, family, run_id, strategy)
            metrics_path = artifact_dir / "metrics.json"
            if metrics_path.is_file():
                refs.append(
                    BaselineMetricsRef(
                        family=family,
                        run_id=run_id,
                        strategy=strategy,
                        metrics_path=metrics_path,
                        artifact_dir=artifact_dir,
                    )
                )
    return refs


def load_metrics_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"metrics.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _run_dir_candidates(repo_root: Path, family: str) -> list[Path]:
    family_dir = repo_root / "artifacts" / f"v2_{family}"
    if not family_dir.is_dir():
        return []
    pinned = EXTENDED_RUN_IDS.get(family)
    if pinned:
        pinned_dir = family_dir / pinned
        if pinned_dir.is_dir():
            rest = sorted(
                [p for p in family_dir.iterdir() if p.is_dir() and p.name != pinned],
                key=lambda p: p.name,
                reverse=True,
            )
            return [pinned_dir, *rest]
    return sorted(
        [p for p in family_dir.iterdir() if p.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    )


def _latest_run_metrics_entries(
    repo_root: Path,
    family: str,
) -> list[dict[str, Any]]:
    """Metrics for the newest run directory under artifacts/v2_<family> that has strategy folders."""
    run_dirs = _run_dir_candidates(repo_root, family)
    for run_dir in run_dirs:
        refs: list[dict[str, Any]] = []
        for strategy in STRATEGIES:
            artifact_dir = run_dir / strategy
            metrics_path = artifact_dir / "metrics.json"
            if not metrics_path.is_file():
                continue
            metrics = load_metrics_json(metrics_path)
            test = metrics.get("test") or {}
            refs.append(
                {
                    "family": family,
                    "run_id": run_dir.name,
                    "split_strategy": strategy,
                    "artifact_dir": str(artifact_dir.relative_to(repo_root)),
                    "metrics_path": str(metrics_path.relative_to(repo_root)),
                    "assignment_sha256": metrics.get("assignment_sha256"),
                    "counts": metrics.get("counts"),
                    "test": test,
                }
            )
        if refs:
            return refs
    return []


def extended_metrics_entries(repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Baseline frozen runs plus optional mlp/gbdt/tcn when trained artifacts exist."""
    root = repo_root or REPO_ROOT
    entries = baseline_metrics_entries(root)
    seen = {(e["family"], e["run_id"]) for e in entries}
    for family in EXTENDED_FAMILIES:
        batch = _latest_run_metrics_entries(root, family)
        if not batch:
            continue
        key = (family, batch[0]["run_id"])
        if key in seen:
            continue
        entries.extend(batch)
        seen.add(key)
    return entries


def baseline_metrics_entries(repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Load all baseline metrics.json files with model metadata."""
    root = repo_root or REPO_ROOT
    entries: list[dict[str, Any]] = []
    for ref in iter_baseline_metrics_refs(root):
        metrics = load_metrics_json(ref.metrics_path)
        test = metrics.get("test") or {}
        entries.append(
            {
                "family": ref.family,
                "run_id": ref.run_id,
                "split_strategy": ref.strategy,
                "artifact_dir": str(ref.artifact_dir.relative_to(root)),
                "metrics_path": str(ref.metrics_path.relative_to(root)),
                "assignment_sha256": metrics.get("assignment_sha256"),
                "counts": metrics.get("counts"),
                "test": test,
            }
        )
    return entries


def compute_generalization_gap(in_domain_macro_f1: float, target_macro_f1: float) -> float:
    """Positive gap means in-domain test macro-F1 exceeds the target strategy."""
    return float(in_domain_macro_f1) - float(target_macro_f1)


def macro_f1_from_test_section(test: dict[str, Any] | None) -> float | None:
    if not test:
        return None
    value = test.get("macro_f1")
    return float(value) if value is not None else None


def supplement_macro_averages(test: dict[str, Any]) -> dict[str, Any]:
    """Ensure macro_precision / macro_recall exist (derive from per_class if absent)."""
    enriched = dict(test)
    per_class = enriched.get("per_class") or {}
    if enriched.get("macro_precision") is None and per_class:
        values = [stats["precision"] for stats in per_class.values() if stats.get("precision") is not None]
        if values:
            enriched["macro_precision"] = float(sum(values) / len(values))
    if enriched.get("macro_recall") is None and per_class:
        values = [stats["recall"] for stats in per_class.values() if stats.get("recall") is not None]
        if values:
            enriched["macro_recall"] = float(sum(values) / len(values))
    return enriched


def confused_pairs_from_matrix(
    confusion: dict[str, Any] | None,
    *,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Return off-diagonal confused label pairs sorted by count descending."""
    if not confusion:
        return []
    labels = list(confusion.get("labels") or [])
    matrix = confusion.get("matrix") or []
    pairs: list[dict[str, Any]] = []
    for i, row in enumerate(matrix):
        for j, count in enumerate(row):
            if i == j or not count:
                continue
            pairs.append(
                {
                    "true_label": labels[i] if i < len(labels) else str(i),
                    "predicted_label": labels[j] if j < len(labels) else str(j),
                    "count": int(count),
                }
            )
    pairs.sort(key=lambda item: item["count"], reverse=True)
    return pairs[:top_k]


def build_generalization_rows(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach generalization gaps vs in-domain macro-F1 per model family."""
    in_domain_by_family: dict[str, float] = {}
    for entry in entries:
        if entry["split_strategy"] != "in_domain":
            continue
        macro = macro_f1_from_test_section(entry.get("test"))
        if macro is not None:
            in_domain_by_family[entry["family"]] = macro

    rows: list[dict[str, Any]] = []
    for entry in entries:
        test = supplement_macro_averages(entry.get("test") or {})
        target_macro = macro_f1_from_test_section(test)
        in_domain_macro = in_domain_by_family.get(entry["family"])
        gap = None
        if in_domain_macro is not None and target_macro is not None:
            gap = compute_generalization_gap(in_domain_macro, target_macro)
        per_class = test.get("per_class") or {}
        rows.append(
            {
                "model_id": f"v2_{entry['family']}_{entry['split_strategy']}_{entry['run_id']}",
                "family": entry["family"],
                "run_id": entry["run_id"],
                "split_strategy": entry["split_strategy"],
                "artifact_dir": entry["artifact_dir"],
                "assignment_sha256": entry.get("assignment_sha256"),
                "counts": entry.get("counts"),
                "accuracy": test.get("accuracy"),
                "macro_f1": target_macro,
                "macro_precision": test.get("macro_precision"),
                "macro_recall": test.get("macro_recall"),
                "weighted_f1": test.get("weighted_f1"),
                "per_class": per_class,
                "confusion_matrix": test.get("confusion_matrix"),
                "confused_pairs": confused_pairs_from_matrix(test.get("confusion_matrix")),
                "in_domain_macro_f1": in_domain_macro,
                "generalization_gap": gap,
            }
        )
    return rows
