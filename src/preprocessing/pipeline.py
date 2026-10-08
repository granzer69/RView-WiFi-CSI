"""Validation, optional cleaning, normalization, and in-session windowing.

The order is fixed:

1. Validate the canonical window.
2. Optionally clip amplitude outliers with a median absolute deviation rule.
3. Optionally z-score that same window.
4. Cut temporal segments that stay inside the window.

Clipping and z-scoring are off unless a config turns them on. The default
result is the original trial as one segment. A segment never takes samples
from two sessions, because the input is already one session and the cutter
does not look at any other window.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from common.errors import DatasetError
from ingestion.schema import CsiWindow

_NORMALIZERS = ("none", "per_window_zscore")


@dataclass(frozen=True)
class PreprocessConfig:
    """Switches for the four preprocessing steps."""

    clip_mad: bool = False
    mad_k: float = 5.0
    normalize: str = "none"
    window_length: int | None = None
    hop: int | None = None

    def __post_init__(self) -> None:
        if self.normalize not in _NORMALIZERS:
            raise DatasetError(f"normalize must be one of {_NORMALIZERS}, got {self.normalize!r}")
        if self.mad_k <= 0:
            raise DatasetError("mad_k must be positive")
        if self.window_length is None:
            if self.hop is not None:
                raise DatasetError("hop is only used when window_length is set")
            return
        if self.window_length < 1:
            raise DatasetError("window_length must be at least 1")
        hop = self.window_length if self.hop is None else self.hop
        if hop < 1 or hop > self.window_length:
            raise DatasetError("hop must satisfy 1 <= hop <= window_length")
        object.__setattr__(self, "hop", hop)

    def to_dict(self) -> dict[str, object]:
        return {
            "clip_mad": self.clip_mad,
            "mad_k": self.mad_k,
            "normalize": self.normalize,
            "window_length": self.window_length,
            "hop": self.hop,
        }


@dataclass(frozen=True)
class PreprocessResult:
    windows: tuple[CsiWindow, ...]
    dropped_tail: int


def process(window: CsiWindow, config: PreprocessConfig | None = None) -> PreprocessResult:
    """Return new windows. The input array is not modified."""
    settings = config or PreprocessConfig()
    _validate(window)
    amplitude = np.array(window.amplitude, dtype=np.float64, copy=True)
    if settings.clip_mad:
        amplitude = _clip_mad(amplitude, settings.mad_k)
    if settings.normalize == "per_window_zscore":
        amplitude = _zscore(amplitude)
    segments, dropped = _segment(amplitude, settings.window_length, settings.hop)
    built = tuple(
        _segment_window(window, segment, start, index, len(segments), settings)
        for index, (start, segment) in enumerate(segments)
    )
    return PreprocessResult(windows=built, dropped_tail=dropped)


def processed_hash(result: PreprocessResult) -> str:
    """Hash segment bytes in order. Same input and config produce the same hash."""
    digest = hashlib.sha256()
    digest.update(str(result.dropped_tail).encode("ascii"))
    for window in result.windows:
        array = np.ascontiguousarray(window.amplitude)
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _validate(window: CsiWindow) -> None:
    if window.n_times < 1 or window.subcarriers < 1:
        raise DatasetError("window has no samples")
    if window.amplitude.shape != (window.n_times, window.subcarriers):
        raise DatasetError(f"unexpected amplitude shape {window.amplitude.shape}")


def _clip_mad(amplitude: np.ndarray, mad_k: float) -> np.ndarray:
    median = float(np.median(amplitude))
    mad = float(np.median(np.abs(amplitude - median)))
    if mad == 0.0:
        return amplitude
    lower = median - mad_k * mad
    upper = median + mad_k * mad
    return np.clip(amplitude, lower, upper)


def _zscore(amplitude: np.ndarray) -> np.ndarray:
    mean = float(amplitude.mean())
    std = float(amplitude.std())
    if std == 0.0:
        return np.zeros_like(amplitude)
    return (amplitude - mean) / std


def _segment(
    amplitude: np.ndarray,
    window_length: int | None,
    hop: int | None,
) -> tuple[list[tuple[int, np.ndarray]], int]:
    n_times = int(amplitude.shape[0])
    if window_length is None:
        return [(0, amplitude)], 0
    assert hop is not None
    if window_length > n_times:
        raise DatasetError(
            f"window_length {window_length} is longer than this session ({n_times} samples)"
        )
    pieces: list[tuple[int, np.ndarray]] = []
    start = 0
    while start + window_length <= n_times:
        pieces.append((start, amplitude[start : start + window_length]))
        start += hop
    return pieces, n_times - start


def _segment_window(
    source: CsiWindow,
    amplitude: np.ndarray,
    start: int,
    index: int,
    n_segments: int,
    settings: PreprocessConfig,
) -> CsiWindow:
    metadata = dict(source.metadata)
    metadata["preprocess"] = settings.to_dict()
    metadata["segment_index"] = index
    metadata["segment_count"] = n_segments
    metadata["segment_start"] = start
    metadata["segment_end"] = start + int(amplitude.shape[0])
    return CsiWindow(
        amplitude=amplitude,
        phase=None if source.phase is None else np.array(source.phase[start : start + amplitude.shape[0]], copy=True),
        sample_rate_hz=source.sample_rate_hz,
        timestamp=source.timestamp,
        subcarriers=source.subcarriers,
        antennas=source.antennas,
        metadata=metadata,
    )
