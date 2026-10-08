"""Read-only numeric and split audits for ESP-Fi HAR."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from datasets.esp_fi import SUBCARRIERS, TIME_STEPS, TrialRecord, load_window
from datasets.splits import SPLIT_NAMES, SplitAssignment

NEAR_CONSTANT_STD = 1e-9


@dataclass(frozen=True)
class NumericAudit:
    files_read: int
    dtype: str
    non_finite_count: int
    unique_shapes: dict[str, int]
    amplitude_min: float
    amplitude_max: float
    amplitude_mean: float
    amplitude_std: float
    per_subcarrier_mean: list[float]
    per_subcarrier_std: list[float]
    recordings_with_constant_subcarrier: int
    recordings_with_near_constant_subcarrier: int
    max_constant_subcarriers_in_one_recording: int
    per_recording_amplitude_min: float
    per_recording_amplitude_max: float
    per_recording_mean_min: float
    per_recording_mean_max: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_read": self.files_read,
            "dtype": self.dtype,
            "non_finite_count": self.non_finite_count,
            "unique_shapes": self.unique_shapes,
            "amplitude_min": self.amplitude_min,
            "amplitude_max": self.amplitude_max,
            "amplitude_mean": self.amplitude_mean,
            "amplitude_std": self.amplitude_std,
            "per_subcarrier_mean": self.per_subcarrier_mean,
            "per_subcarrier_std": self.per_subcarrier_std,
            "recordings_with_constant_subcarrier": self.recordings_with_constant_subcarrier,
            "recordings_with_near_constant_subcarrier": self.recordings_with_near_constant_subcarrier,
            "max_constant_subcarriers_in_one_recording": self.max_constant_subcarriers_in_one_recording,
            "per_recording_amplitude_min": self.per_recording_amplitude_min,
            "per_recording_amplitude_max": self.per_recording_amplitude_max,
            "per_recording_mean_min": self.per_recording_mean_min,
            "per_recording_mean_max": self.per_recording_mean_max,
            "near_constant_std_threshold": NEAR_CONSTANT_STD,
            "expected_shape": [TIME_STEPS, SUBCARRIERS],
        }


def audit_numeric(
    records: list[TrialRecord],
    *,
    loader: Callable[[TrialRecord], Any] | None = None,
) -> NumericAudit:
    """Scan every trial matrix without modifying files."""
    load = loader or load_window
    shapes: Counter[str] = Counter()
    non_finite = 0
    gmin = gmax = None
    count = 0
    sum_x = np.zeros(SUBCARRIERS, dtype=np.float64)
    sum_x2 = np.zeros(SUBCARRIERS, dtype=np.float64)
    dtype_name = "float64"
    rec_min = rec_max = None
    rec_mean_min = rec_mean_max = None
    with_const = 0
    with_near_const = 0
    max_const_in_one = 0

    for record in records:
        window = load(record)
        values = window.amplitude
        shapes[str(tuple(values.shape))] += 1
        non_finite += int(np.size(values) - np.isfinite(values).sum())
        batch_min = float(values.min())
        batch_max = float(values.max())
        batch_mean = float(values.mean())
        gmin = batch_min if gmin is None else min(gmin, batch_min)
        gmax = batch_max if gmax is None else max(gmax, batch_max)
        rec_min = batch_min if rec_min is None else min(rec_min, batch_min)
        rec_max = batch_max if rec_max is None else max(rec_max, batch_max)
        rec_mean_min = batch_mean if rec_mean_min is None else min(rec_mean_min, batch_mean)
        rec_mean_max = batch_mean if rec_mean_max is None else max(rec_mean_max, batch_mean)
        count += int(values.size)
        sum_x += values.sum(axis=0)
        sum_x2 += (values ** 2).sum(axis=0)
        col_std = values.std(axis=0)
        n_const = int(np.sum(col_std == 0.0))
        n_near = int(np.sum(col_std < NEAR_CONSTANT_STD))
        if n_const:
            with_const += 1
        if n_near:
            with_near_const += 1
        max_const_in_one = max(max_const_in_one, n_const)

    assert count > 0
    n_points_per_subcarrier = len(records) * TIME_STEPS
    mean_all = float(sum_x.sum() / count)
    per_sc_mean = (sum_x / n_points_per_subcarrier).tolist()
    per_sc_std = np.sqrt(
        np.maximum(sum_x2 / n_points_per_subcarrier - (sum_x / n_points_per_subcarrier) ** 2, 0.0)
    ).tolist()
    variance = (sum_x2.sum() / count) - mean_all ** 2
    return NumericAudit(
        files_read=sum(shapes.values()),
        dtype=dtype_name,
        non_finite_count=non_finite,
        unique_shapes=dict(shapes),
        amplitude_min=gmin if gmin is not None else 0.0,
        amplitude_max=gmax if gmax is not None else 0.0,
        amplitude_mean=mean_all,
        amplitude_std=float(np.sqrt(max(variance, 0.0))),
        per_subcarrier_mean=per_sc_mean,
        per_subcarrier_std=per_sc_std,
        recordings_with_constant_subcarrier=with_const,
        recordings_with_near_constant_subcarrier=with_near_const,
        max_constant_subcarriers_in_one_recording=max_const_in_one,
        per_recording_amplitude_min=rec_min if rec_min is not None else 0.0,
        per_recording_amplitude_max=rec_max if rec_max is not None else 0.0,
        per_recording_mean_min=rec_mean_min if rec_mean_min is not None else 0.0,
        per_recording_mean_max=rec_mean_max if rec_mean_max is not None else 0.0,
    )


def session_leakage_answer(assignment: SplitAssignment) -> dict[str, Any]:
    """Document whether the same recording can appear in train and test."""
    sessions_per_split: dict[str, set[str]] = {name: set() for name in SPLIT_NAMES}
    for session_id, split_name in assignment.session_to_split.items():
        sessions_per_split[split_name].add(session_id)
    overlap_train_test = sessions_per_split["train"] & sessions_per_split["test"]
    overlap_train_val = sessions_per_split["train"] & sessions_per_split["val"]
    overlap_val_test = sessions_per_split["val"] & sessions_per_split["test"]
    return {
        "split_unit": "one trial file (session_id = stem X-Y-Z-M)",
        "trial_file_cut_across_splits": False,
        "shared_sessions_train_test": sorted(overlap_train_test),
        "shared_sessions_train_val": sorted(overlap_train_val),
        "shared_sessions_val_test": sorted(overlap_val_test),
        "same_recording_leaks_train_and_test": bool(overlap_train_test),
        "protocol_answer": "NO — each session_id maps to exactly one split; a trial file is never divided.",
    }


def audit_split_assignment(
    records: list[TrialRecord],
    assignment: SplitAssignment,
) -> dict[str, Any]:
    """Per-split counts for sessions, users, environments, and classes."""
    by_split: dict[str, list[TrialRecord]] = {name: [] for name in SPLIT_NAMES}
    for record in records:
        by_split[assignment.session_to_split[record.session_id]].append(record)

    def summarize(rows: list[TrialRecord]) -> dict[str, Any]:
        return {
            "samples": len(rows),
            "sessions": len({r.session_id for r in rows}),
            "participants": sorted({r.participant_id for r in rows}),
            "participant_count": len({r.participant_id for r in rows}),
            "scenarios": sorted({r.scenario_id for r in rows}),
            "scenario_count": len({r.scenario_id for r in rows}),
            "by_dataset_label": dict(sorted(Counter(r.dataset_label for r in rows).items())),
            "by_normalized_label": dict(sorted(Counter(r.normalized_label for r in rows).items())),
        }

    groups: dict[str, set[str]] = defaultdict(set)
    for record in records:
        groups[assignment.session_to_split[record.session_id]].add(record.group_value(assignment.strategy))

    cross_split_groups: list[str] = []
    group_to_splits: dict[str, set[str]] = defaultdict(set)
    for record in records:
        group_to_splits[record.group_value(assignment.strategy)].add(
            assignment.session_to_split[record.session_id]
        )
    cross_split_groups = sorted(g for g, splits in group_to_splits.items() if len(splits) != 1)

    return {
        "strategy": assignment.strategy,
        "seed": assignment.seed,
        "counts": assignment.counts(),
        "per_split": {name: summarize(by_split[name]) for name in SPLIT_NAMES},
        "groups_crossing_splits": cross_split_groups,
        "session_integrity": session_leakage_answer(assignment),
    }
