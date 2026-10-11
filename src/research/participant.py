"""Participant metadata and test-only per-user metrics."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np

from api.model_registry import _load_backend
from datasets.esp_fi import discover_trials
from datasets.splits import assign_splits
from evaluation.metrics import classification_report_dict
from ingestion.ml_contract import NORMALIZED_LABELS, HarSample
from research.generalization import BASELINE_RUN_IDS, baseline_artifact_dir
from training.esp_fi import load_esp_fi_split_bundle

ProfileStatus = Literal["ok", "blocked", "not_evaluated"]


@dataclass(frozen=True)
class DataAvailability:
    present: bool
    root: Path
    reason: str | None = None


def esp_fi_data_root(repo_root: Path) -> Path:
    return repo_root / "data" / "raw" / "esp-fi-har"


def check_esp_fi_available(repo_root: Path) -> DataAvailability:
    root = esp_fi_data_root(repo_root)
    if not root.is_dir():
        return DataAvailability(
            present=False,
            root=root,
            reason=f"ESP-Fi data root not found: {root}",
        )
    return DataAvailability(present=True, root=root)


def build_participant_overview(
    repo_root: Path,
    *,
    strategy: str = "in_domain",
    seed: int = 42,
) -> dict[str, Any]:
    """Session counts per participant from discover_trials + assign_splits."""
    availability = check_esp_fi_available(repo_root)
    if not availability.present:
        return {
            "status": "blocked",
            "reason": availability.reason,
            "participants": [],
        }

    records = discover_trials(availability.root)
    assignment = assign_splits(records, strategy=strategy, seed=seed)
    by_user: dict[int, dict[str, Any]] = {}
    for record in records:
        split_name = assignment.session_to_split[record.session_id]
        user_id = record.participant_id
        bucket = by_user.setdefault(
            user_id,
            {
                "user_id": user_id,
                "session_counts": {"train": 0, "val": 0, "test": 0, "total": 0},
                "scenarios": set(),
                "activities": set(),
            },
        )
        bucket["session_counts"][split_name] += 1
        bucket["session_counts"]["total"] += 1
        bucket["scenarios"].add(record.scenario_id)
        bucket["activities"].add(record.normalized_label)

    participants = []
    for user_id in sorted(by_user):
        row = by_user[user_id]
        participants.append(
            {
                "user_id": user_id,
                "session_counts": row["session_counts"],
                "scenario_ids": sorted(row["scenarios"]),
                "activities": sorted(row["activities"]),
            }
        )

    return {
        "status": "ok",
        "split_strategy": strategy,
        "participants": participants,
        "trial_count": len(records),
    }


def _group_test_samples_by_user(samples: tuple[HarSample, ...]) -> dict[int, list[HarSample]]:
    groups: dict[int, list[HarSample]] = defaultdict(list)
    for sample in samples:
        if sample.split != "test":
            continue
        groups[int(sample.user_id)].append(sample)
    return dict(groups)


def _predict_labels(backend: Any, amplitudes: np.ndarray) -> np.ndarray:
    if hasattr(backend, "predict"):
        return np.asarray(backend.predict(amplitudes), dtype=np.int64)
    proba = np.asarray(backend.predict_proba(amplitudes))
    return np.argmax(proba, axis=1).astype(np.int64)


def per_participant_test_metrics_for_model(
    repo_root: Path,
    *,
    family: str,
    strategy: str,
    run_id: str | None = None,
    verify_assignment_hash: bool = True,
) -> dict[str, Any]:
    """Evaluate a saved baseline model on test-split sessions grouped by user_id."""
    availability = check_esp_fi_available(repo_root)
    if not availability.present:
        return {"status": "blocked", "reason": availability.reason, "participants": []}

    resolved_run = run_id or BASELINE_RUN_IDS.get(family)
    if not resolved_run:
        return {"status": "blocked", "reason": f"unknown family {family}", "participants": []}

    artifact_dir = baseline_artifact_dir(repo_root, family, resolved_run, strategy)
    if not artifact_dir.is_dir():
        return {
            "status": "blocked",
            "reason": f"artifact directory missing: {artifact_dir}",
            "participants": [],
        }

    bundle = load_esp_fi_split_bundle(
        availability.root,
        strategy=strategy,
        verify_assignment_hash=verify_assignment_hash,
    )
    test_samples = bundle.samples_by_split.get("test", ())
    groups = _group_test_samples_by_user(test_samples)

    backend = _load_backend(family, artifact_dir)
    label_names = tuple(getattr(backend, "label_names", ()))

    participant_metrics: list[dict[str, Any]] = []
    for user_id in sorted(groups):
        items = groups[user_id]
        amplitudes = np.stack([sample.amplitude for sample in items], axis=0)
        labels = np.asarray([sample.label_id for sample in items], dtype=np.int64)
        predictions = _predict_labels(backend, amplitudes)
        report = classification_report_dict(
            labels,
            predictions,
            labels=label_names if label_names else NORMALIZED_LABELS,
        )
        participant_metrics.append(
            {
                "user_id": user_id,
                "test_session_count": len(items),
                "accuracy": report["accuracy"],
                "macro_f1": report["macro_f1"],
                "weighted_f1": report["weighted_f1"],
                "per_class": report["per_class"],
            }
        )

    return {
        "status": "ok",
        "family": family,
        "run_id": resolved_run,
        "split_strategy": strategy,
        "artifact_dir": str(artifact_dir.relative_to(repo_root)),
        "participants": participant_metrics,
    }


def build_all_participant_model_metrics(
    repo_root: Path,
    *,
    strategies: tuple[str, ...] = ("in_domain",),
    families: tuple[str, ...] = ("logreg", "rf", "cnn1d", "gru"),
) -> dict[str, Any]:
    availability = check_esp_fi_available(repo_root)
    if not availability.present:
        return {
            "status": "blocked",
            "reason": availability.reason,
            "models": [],
        }

    models: list[dict[str, Any]] = []
    for family in families:
        for strategy in strategies:
            result = per_participant_test_metrics_for_model(
                repo_root,
                family=family,
                strategy=strategy,
            )
            if result.get("status") == "ok":
                models.append(result)

    return {
        "status": "ok" if models else "not_evaluated",
        "models": models,
        "methodology": (
            "Per-participant metrics use only sessions assigned to the test split. "
            "Predictions are regenerated from frozen baseline artifacts; train/val "
            "sessions are excluded."
        ),
    }


def calib_eval_session_sets_disjoint(
    calib_session_ids: set[str],
    eval_session_ids: set[str],
) -> bool:
    """True when calibration and evaluation session sets do not overlap."""
    return calib_session_ids.isdisjoint(eval_session_ids)
