"""Load ESP-Fi trials into HarSample bundles per split strategy."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from common.errors import DatasetError, SplitError
from datasets.esp_fi import discover_trials, load_window
from datasets.splits import SplitAssignment, assign_splits
from ingestion.ml_contract import HarSample, har_sample_from_window
from preprocessing.pipeline import PreprocessConfig, process

EXPECTED_ASSIGNMENT_SHA256: dict[str, str] = {
    "in_domain": "6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da",
    "cross_user": "ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72",
    "cross_environment": "00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8",
}


def assignment_sha256(assignment: SplitAssignment) -> str:
    lines = [f"{session}\t{split}" for session, split in sorted(assignment.session_to_split.items())]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EspFiSplitBundle:
    strategy: str
    assignment: SplitAssignment
    samples_by_split: dict[str, tuple[HarSample, ...]]

    def amplitudes_and_labels(self, split: str) -> tuple[np.ndarray, np.ndarray]:
        samples = self.samples_by_split[split]
        if not samples:
            raise DatasetError(f"no samples for split {split!r}")
        amplitudes = np.stack([sample.amplitude for sample in samples], axis=0)
        labels = np.asarray([sample.label_id for sample in samples], dtype=np.int64)
        return amplitudes, labels


def load_esp_fi_split_bundle(
    root: Path,
    *,
    strategy: str,
    seed: int = 42,
    test_fraction: float = 0.15,
    val_fraction: float = 0.15,
    preprocess: PreprocessConfig | None = None,
    verify_assignment_hash: bool = True,
) -> EspFiSplitBundle:
    records = discover_trials(root)
    assignment = assign_splits(
        records,
        strategy=strategy,
        seed=seed,
        test_fraction=test_fraction,
        val_fraction=val_fraction,
    )
    digest = assignment_sha256(assignment)
    expected = EXPECTED_ASSIGNMENT_SHA256.get(strategy)
    if verify_assignment_hash and expected is not None and digest != expected:
        raise SplitError(
            f"assignment hash for {strategy} is {digest}, expected locked hash {expected}"
        )

    settings = preprocess or PreprocessConfig()
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


def bundle_summary(bundle: EspFiSplitBundle) -> dict[str, Any]:
    return {
        "strategy": bundle.strategy,
        "assignment_sha256": assignment_sha256(bundle.assignment),
        "counts": bundle.assignment.counts(),
    }
