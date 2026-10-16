"""LOUO ESP-Fi bundles (session-safe leave-one-user-out)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common.errors import DatasetError, SplitError
from datasets.esp_fi import discover_trials, load_window
from datasets.splits import SplitAssignment, assign_louo_splits, louo_strategy_name
from ingestion.ml_contract import HarSample, har_sample_from_window
from preprocessing.pipeline import PreprocessConfig, process
from training.esp_fi import EspFiSplitBundle, assignment_sha256

_LOUO_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "experiments" / "esp_fi_louo_splits.json"


def _load_locked_hashes() -> dict[int, str]:
    payload = json.loads(_LOUO_CONFIG_PATH.read_text(encoding="utf-8"))
    raw = payload.get("locked_assignment_sha256") or {}
    return {int(key): str(value) for key, value in raw.items()}


EXPECTED_LOUO_ASSIGNMENT_SHA256: dict[int, str] = _load_locked_hashes()


def load_esp_fi_louo_bundle(
    root: Path,
    *,
    held_out_participant: int,
    seed: int = 42,
    val_fraction: float = 0.15,
    preprocess: PreprocessConfig | None = None,
    verify_assignment_hash: bool = True,
) -> EspFiSplitBundle:
    records = discover_trials(root)
    assignment = assign_louo_splits(
        records,
        held_out_participant=held_out_participant,
        seed=seed,
        val_fraction=val_fraction,
    )
    digest = assignment_sha256(assignment)
    expected = EXPECTED_LOUO_ASSIGNMENT_SHA256.get(held_out_participant)
    if verify_assignment_hash and expected is not None and digest != expected:
        raise SplitError(
            f"LOUO assignment hash for user {held_out_participant} is {digest}, expected {expected}"
        )

    settings = preprocess or PreprocessConfig()
    strategy = louo_strategy_name(held_out_participant)
    by_split: dict[str, list[HarSample]] = {"train": [], "val": [], "test": []}
    for record in records:
        split_name = assignment.session_to_split[record.session_id]
        window = load_window(record)
        result = process(window, settings)
        if len(result.windows) != 1:
            raise DatasetError(
                f"expected one segment per trial for {record.session_id}, got {len(result.windows)}"
            )
        sample = har_sample_from_window(
            result.windows[0],
            split=split_name,
            split_strategy=strategy,
        )
        by_split[split_name].append(sample)

    for split_name, items in by_split.items():
        items.sort(key=lambda sample: sample.session_id)

    return EspFiSplitBundle(
        strategy=strategy,
        assignment=assignment,
        samples_by_split={name: tuple(items) for name, items in by_split.items()},
    )


def louo_bundle_summary(bundle: EspFiSplitBundle, held_out_participant: int) -> dict[str, Any]:
    return {
        "strategy": bundle.strategy,
        "held_out_participant": held_out_participant,
        "assignment_sha256": assignment_sha256(bundle.assignment),
        "counts": bundle.assignment.counts(),
    }
