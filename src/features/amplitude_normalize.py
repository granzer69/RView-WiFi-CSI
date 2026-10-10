"""Train-only amplitude normalization for deep models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from common.errors import DatasetError


@dataclass
class AmplitudeNormalizer:
    """Per-subcarrier mean and scale fit on training amplitudes only."""

    mean_: np.ndarray | None = None
    scale_: np.ndarray | None = None

    def fit(self, amplitudes: np.ndarray) -> AmplitudeNormalizer:
        array = np.asarray(amplitudes, dtype=np.float64)
        if array.ndim != 3:
            raise DatasetError(f"expected 3D amplitudes (N, time, subcarriers), got {array.shape}")
        # Collapse batch and time; one statistic per subcarrier.
        self.mean_ = array.mean(axis=(0, 1))
        self.scale_ = array.std(axis=(0, 1))
        self.scale_[self.scale_ == 0.0] = 1.0
        return self

    def transform(self, amplitudes: np.ndarray) -> np.ndarray:
        if self.mean_ is None or self.scale_ is None:
            raise DatasetError("normalizer is not fitted")
        array = np.asarray(amplitudes, dtype=np.float64)
        if array.ndim == 2:
            return (array - self.mean_) / self.scale_
        if array.ndim != 3:
            raise DatasetError(f"expected 2D or 3D amplitudes, got {array.shape}")
        return (array - self.mean_) / self.scale_

    def to_dict(self) -> dict[str, Any]:
        if self.mean_ is None or self.scale_ is None:
            raise DatasetError("normalizer is not fitted")
        return {"mean": self.mean_.tolist(), "scale": self.scale_.tolist()}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AmplitudeNormalizer:
        return cls(
            mean_=np.asarray(payload["mean"], dtype=np.float64),
            scale_=np.asarray(payload["scale"], dtype=np.float64),
        )
