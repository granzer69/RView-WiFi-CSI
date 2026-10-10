"""Per-trial statistical and spectral features from amplitude CSI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

from common.errors import DatasetError

# Feature groups documented for experiment proposals and manifests.
PER_SUBCARRIER_STATS = (
    "mean",
    "std",
    "var",
    "min",
    "max",
    "range",
    "rms",
    "energy",
    "skew",
    "kurt",
)
GLOBAL_STATS = PER_SUBCARRIER_STATS + ("entropy",)
SPECTRAL_STATS = ("fft_mean", "fft_std")


def _safe_skew(values: np.ndarray) -> float:
    if values.size < 3 or float(np.std(values)) == 0.0:
        return 0.0
    return float(stats.skew(values, bias=False))


def _safe_kurt(values: np.ndarray) -> float:
    if values.size < 4 or float(np.std(values)) == 0.0:
        return 0.0
    return float(stats.kurtosis(values, bias=False))


def _histogram_entropy(values: np.ndarray, bins: int = 32) -> float:
    counts, _ = np.histogram(values, bins=bins)
    total = float(counts.sum())
    if total == 0.0:
        return 0.0
    probs = counts.astype(np.float64) / total
    probs = probs[probs > 0]
    return float(-(probs * np.log2(probs)).sum())


def classical_feature_vector(amplitude: np.ndarray) -> np.ndarray:
    """Extract a fixed-length feature vector from ``(time, subcarriers)`` amplitude."""
    array = np.asarray(amplitude, dtype=np.float64)
    if array.ndim != 2:
        raise DatasetError(f"amplitude must be 2D, got {array.shape}")
    if not np.isfinite(array).all():
        raise DatasetError("amplitude contains non-finite values")

    time_axis = array
    subcarrier_axis = array.T
    pieces: list[np.ndarray] = []

    for sub in subcarrier_axis:
        pieces.append(
            np.array(
                [
                    float(sub.mean()),
                    float(sub.std()),
                    float(sub.var()),
                    float(sub.min()),
                    float(sub.max()),
                    float(sub.max() - sub.min()),
                    float(np.sqrt(np.mean(sub ** 2))),
                    float(np.sum(sub ** 2)),
                    _safe_skew(sub),
                    _safe_kurt(sub),
                ],
                dtype=np.float64,
            )
        )

    flat = array.reshape(-1)
    pieces.append(
        np.array(
            [
                float(flat.mean()),
                float(flat.std()),
                float(flat.var()),
                float(flat.min()),
                float(flat.max()),
                float(flat.max() - flat.min()),
                float(np.sqrt(np.mean(flat ** 2))),
                float(np.sum(flat ** 2)),
                _safe_skew(flat),
                _safe_kurt(flat),
                _histogram_entropy(flat),
            ],
            dtype=np.float64,
        )
    )

    spectrum = np.abs(np.fft.rfft(time_axis, axis=0))
    pieces.append(spectrum.mean(axis=0))
    pieces.append(spectrum.std(axis=0))

    return np.concatenate(pieces)


def classical_feature_dim(n_subcarriers: int) -> int:
    return len(PER_SUBCARRIER_STATS) * n_subcarriers + len(GLOBAL_STATS) + len(SPECTRAL_STATS) * n_subcarriers


@dataclass
class ClassicalFeatureExtractor:
    """Standardize classical features; fit statistics on training data only."""

    mean_: np.ndarray | None = None
    scale_: np.ndarray | None = None

    @property
    def n_features(self) -> int:
        if self.mean_ is None:
            raise DatasetError("extractor is not fitted")
        return int(self.mean_.shape[0])

    def feature_metadata(self, n_subcarriers: int) -> dict[str, Any]:
        names: list[str] = []
        for stat in PER_SUBCARRIER_STATS:
            for index in range(n_subcarriers):
                names.append(f"sc{index}_{stat}")
        for stat in GLOBAL_STATS:
            names.append(f"global_{stat}")
        for stat in SPECTRAL_STATS:
            for index in range(n_subcarriers):
                names.append(f"sc{index}_{stat}")
        if len(names) != classical_feature_dim(n_subcarriers):
            raise DatasetError("feature name layout does not match dimension")
        return {
            "kind": "classical_v1",
            "per_subcarrier_stats": list(PER_SUBCARRIER_STATS),
            "global_stats": list(GLOBAL_STATS),
            "spectral_stats": list(SPECTRAL_STATS),
            "n_subcarriers": n_subcarriers,
            "n_features": len(names),
            "feature_names": names,
        }

    def fit(self, amplitudes: np.ndarray) -> ClassicalFeatureExtractor:
        matrix = _stack_features(amplitudes)
        self.mean_ = matrix.mean(axis=0)
        self.scale_ = matrix.std(axis=0)
        self.scale_[self.scale_ == 0.0] = 1.0
        return self

    def transform(self, amplitudes: np.ndarray) -> np.ndarray:
        if self.mean_ is None or self.scale_ is None:
            raise DatasetError("extractor is not fitted")
        matrix = _stack_features(amplitudes)
        return (matrix - self.mean_) / self.scale_

    def fit_transform(self, amplitudes: np.ndarray) -> np.ndarray:
        return self.fit(amplitudes).transform(amplitudes)

    def to_dict(self) -> dict[str, Any]:
        if self.mean_ is None or self.scale_ is None:
            raise DatasetError("extractor is not fitted")
        return {
            "mean": self.mean_.tolist(),
            "scale": self.scale_.tolist(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ClassicalFeatureExtractor:
        return cls(
            mean_=np.asarray(payload["mean"], dtype=np.float64),
            scale_=np.asarray(payload["scale"], dtype=np.float64),
        )


def _stack_features(amplitudes: np.ndarray) -> np.ndarray:
    if amplitudes.ndim == 2:
        return classical_feature_vector(amplitudes)[None, :]
    if amplitudes.ndim != 3:
        raise DatasetError(f"expected 2D or 3D amplitude batch, got {amplitudes.shape}")
    rows = [classical_feature_vector(sample) for sample in amplitudes]
    return np.vstack(rows)
