"""Model inference helpers."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import numpy as np

from api.model_registry import LoadedModel
from api.spatial import simulated_spatial
from common.errors import DatasetError


def _validate_amplitude(
    amplitude: list[list[float]],
    *,
    max_rows: int,
    max_subcarriers: int,
) -> np.ndarray:
    if len(amplitude) > max_rows:
        raise DatasetError(f"amplitude exceeds max rows ({max_rows})")
    row_len = len(amplitude[0])
    if row_len > max_subcarriers:
        raise DatasetError(f"amplitude exceeds max subcarriers ({max_subcarriers})")
    for row in amplitude:
        if len(row) != row_len:
            raise DatasetError("amplitude rows must have uniform length")
    array = np.asarray(amplitude, dtype=np.float64)
    if not np.isfinite(array).all():
        raise DatasetError("amplitude contains non-finite values")
    return array


def predict_from_amplitude(
    model: LoadedModel,
    amplitude: list[list[float]],
    *,
    session_id: str,
    environment_id: str,
    time_index: int | None,
    frame_count: int | None,
    max_rows: int,
    max_subcarriers: int,
) -> dict:
    array = _validate_amplitude(
        amplitude,
        max_rows=max_rows,
        max_subcarriers=max_subcarriers,
    )
    batch = array[None, :, :]
    started = time.perf_counter()
    proba = np.asarray(model.backend.predict_proba(batch)[0], dtype=np.float64)
    class_idx = int(np.argmax(proba))
    activity = model.label_names[class_idx]
    confidence = float(proba[class_idx])
    latency_ms = (time.perf_counter() - started) * 1000.0

    idx = time_index if time_index is not None else array.shape[0] - 1
    total = frame_count if frame_count is not None else max(array.shape[0], 1)
    progress = idx / (total - 1) if total > 1 else 0.0

    probabilities = {name: float(proba[i]) for i, name in enumerate(model.label_names)}

    presence = confidence >= 0.2 or activity not in {"empty", "none", "background"}

    return {
        "activity": activity,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "environment_id": environment_id,
        "latency_ms": round(latency_ms, 3),
        "source": "model",
        "presence": presence,
        "probabilities": probabilities,
        "model_version": model.version_label,
        "spatial": simulated_spatial(progress, activity),
    }
