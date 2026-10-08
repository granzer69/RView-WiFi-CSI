"""Model-ready sample contract (V1).

The ML layer must consume ``HarSample`` objects, not ESP-Fi folder paths.
Tensor layout is time-major: ``(n_times, n_subcarriers)`` with
``n_times=950`` and ``n_subcarriers=52`` for ESP-Fi amplitude trials.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from common.errors import DatasetError
from ingestion.schema import CsiWindow

NORMALIZED_LABELS = (
    "running",
    "walking",
    "jumping",
    "squatting",
    "arm_wave",
    "turning",
    "falling",
)

LABEL_TO_ID = {name: index for index, name in enumerate(NORMALIZED_LABELS)}

# Documented input shapes for V2+ models (batch dimension omitted).
MODEL_INPUT_SHAPES: dict[str, dict[str, Any]] = {
    "logistic_regression": {
        "features": "flatten(amplitude) -> vector length 49400",
        "shape": (950 * 52,),
    },
    "random_forest": {
        "features": "flatten(amplitude) -> vector length 49400",
        "shape": (950 * 52,),
    },
    "cnn_1d": {
        "features": "amplitude as (channels=subcarriers, length=time)",
        "shape": (52, 950),
        "note": "Transpose of storage order if the framework expects channels-first.",
    },
    "gru": {
        "features": "amplitude as (time, features=subcarriers)",
        "shape": (950, 52),
        "note": "Matches storage order directly.",
    },
}

SPLIT_NAMES = ("train", "val", "test")
PUBLISHED_SPLIT_ROLE = "leakage_check_only"


@dataclass(frozen=True)
class HarSample:
    """One labeled CSI trial ready for preprocessing and models."""

    amplitude: np.ndarray
    normalized_label: str
    label_id: int
    session_id: str
    user_id: int
    environment_id: int
    activity_code: int
    trial_id: int
    split: str
    split_strategy: str
    dataset_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.normalized_label not in LABEL_TO_ID:
            raise DatasetError(f"unknown normalized label {self.normalized_label!r}")
        if LABEL_TO_ID[self.normalized_label] != self.label_id:
            raise DatasetError("label_id does not match normalized_label")
        if self.split not in SPLIT_NAMES:
            raise DatasetError(f"split must be one of {SPLIT_NAMES}, got {self.split!r}")
        amplitude = np.asarray(self.amplitude, dtype=np.float64)
        if amplitude.ndim != 2:
            raise DatasetError(f"amplitude must be 2D, got {amplitude.shape}")
        if not np.isfinite(amplitude).all():
            raise DatasetError("amplitude contains non-finite values")
        object.__setattr__(self, "amplitude", amplitude)

    @property
    def n_times(self) -> int:
        return int(self.amplitude.shape[0])

    @property
    def n_subcarriers(self) -> int:
        return int(self.amplitude.shape[1])

    def flattened(self) -> np.ndarray:
        return self.amplitude.reshape(-1)

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "environment_id": self.environment_id,
            "activity_code": self.activity_code,
            "trial_id": self.trial_id,
            "normalized_label": self.normalized_label,
            "label_id": self.label_id,
            "split": self.split,
            "split_strategy": self.split_strategy,
            "dataset_id": self.dataset_id,
            "shape_time_subcarrier": [self.n_times, self.n_subcarriers],
            **self.metadata,
        }


def har_sample_from_window(
    window: CsiWindow,
    *,
    split: str,
    split_strategy: str,
) -> HarSample:
    """Build a contract sample from a canonical window and split assignment."""
    meta = dict(window.metadata)
    dataset_id = str(meta.get("dataset_id", ""))
    normalized = str(meta.get("normalized_label", ""))
    if not dataset_id or not normalized:
        raise DatasetError("window metadata missing dataset_id or normalized_label")
    return HarSample(
        amplitude=window.amplitude,
        normalized_label=normalized,
        label_id=LABEL_TO_ID[normalized],
        session_id=str(meta.get("session_id", window.session_id)),
        user_id=int(meta["participant_id"]),
        environment_id=int(meta["scenario_id"]),
        activity_code=int(meta["activity_code"]),
        trial_id=int(meta["trial_id"]),
        split=split,
        split_strategy=split_strategy,
        dataset_id=dataset_id,
        metadata={
            "dataset_label": meta.get("dataset_label"),
            "label_verified_by_folder": meta.get("label_verified_by_folder"),
            "label_map": meta.get("label_map"),
            "readme_label_for_code": meta.get("readme_label_for_code"),
            "scenario_name": meta.get("scenario_name"),
            "source_path": None,
        },
    )
