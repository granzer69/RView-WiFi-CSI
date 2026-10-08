"""Canonical CSI window.

The field set follows the architecture contract. Values come from real
ESP-Fi matrices: amplitude is shaped (time, subcarriers), phase is absent,
antenna count is not stored in the file, and the matrix sample rate is
unknown. Do not fill those with placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from common.errors import DatasetError


@dataclass(frozen=True)
class CsiWindow:
    """One CSI trial or a segment cut from a single trial."""

    amplitude: np.ndarray
    phase: np.ndarray | None
    sample_rate_hz: float | None
    timestamp: str | None
    subcarriers: int
    antennas: int | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        amplitude = np.asarray(self.amplitude, dtype=np.float64)
        if amplitude.ndim != 2:
            raise DatasetError(f"amplitude must be 2D, got shape {amplitude.shape}")
        if amplitude.shape[1] != self.subcarriers:
            raise DatasetError(
                f"subcarriers {self.subcarriers} does not match shape {amplitude.shape}"
            )
        if not np.isfinite(amplitude).all():
            raise DatasetError("amplitude contains non-finite values")
        object.__setattr__(self, "amplitude", amplitude)
        if self.phase is not None:
            phase = np.asarray(self.phase, dtype=np.float64)
            if phase.shape != amplitude.shape:
                raise DatasetError("phase shape does not match amplitude")
            if not np.isfinite(phase).all():
                raise DatasetError("phase contains non-finite values")
            object.__setattr__(self, "phase", phase)
        if self.sample_rate_hz is not None and self.sample_rate_hz <= 0:
            raise DatasetError("sample_rate_hz must be positive when set")

    @property
    def n_times(self) -> int:
        return int(self.amplitude.shape[0])

    @property
    def session_id(self) -> str:
        return str(self.metadata.get("session_id", ""))
