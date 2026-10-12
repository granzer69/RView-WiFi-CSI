"""Model inference helpers."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

import numpy as np

from api.model_registry import LoadedModel
from api.spatial import simulated_spatial
from common.errors import DatasetError
from datasets.esp_fi import SUBCARRIERS, TIME_STEPS

if TYPE_CHECKING:
    from api.config import ApiSettings
    from api.model_registry import ModelRegistry

CLASSICAL_FAMILIES = frozenset({"logreg", "rf", "mlp", "gbdt"})
RAW_AMPLITUDE_FAMILIES = frozenset({"cnn1d", "gru", "tcn"})


def resolve_active_model(
    registry: ModelRegistry,
    settings: ApiSettings,
    *,
    model_id: str | None = None,
) -> LoadedModel:
    """Load the explicitly requested or configured model — no silent fallback."""
    if model_id:
        return registry.load_by_id(model_id)
    if settings.active_model_id:
        return registry.load_by_id(settings.active_model_id)
    active = registry.active()
    if active is not None:
        return active
    return registry.load_default()


def validate_amplitude_for_family(
    family: str,
    array: np.ndarray,
    *,
    max_rows: int,
    max_subcarriers: int,
) -> None:
    if array.ndim != 2:
        raise DatasetError(f"amplitude must be 2D, got shape {array.shape}")
    rows, cols = array.shape
    if rows > max_rows:
        raise DatasetError(f"amplitude exceeds max rows ({max_rows})")
    if cols > max_subcarriers:
        raise DatasetError(f"amplitude exceeds max subcarriers ({max_subcarriers})")
    if cols != SUBCARRIERS:
        raise DatasetError(
            f"amplitude must have {SUBCARRIERS} subcarriers (got {cols})"
        )
    if not np.isfinite(array).all():
        raise DatasetError("amplitude contains non-finite values")
    if family in CLASSICAL_FAMILIES:
        if rows < 1:
            raise DatasetError("classical families require at least one time row")
        if rows > TIME_STEPS:
            raise DatasetError(
                f"classical families expect at most {TIME_STEPS} rows (got {rows})"
            )
    elif family in RAW_AMPLITUDE_FAMILIES:
        if rows < 1:
            raise DatasetError("raw amplitude models require at least one time row")
        if rows > TIME_STEPS:
            raise DatasetError(
                f"raw amplitude models expect at most {TIME_STEPS} rows (got {rows})"
            )
    else:
        raise DatasetError(f"unsupported model family for inference: {family}")


def _validate_amplitude(
    amplitude: list[list[float]],
    *,
    max_rows: int,
    max_subcarriers: int,
) -> np.ndarray:
    if not amplitude:
        raise DatasetError("amplitude must contain at least one row")
    row_len = len(amplitude[0])
    for row in amplitude:
        if len(row) != row_len:
            raise DatasetError("amplitude rows must have uniform length")
    array = np.asarray(amplitude, dtype=np.float64)
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
    replay_source: Literal["model", "dataset_replay"] = "model",
) -> dict:
    array = _validate_amplitude(
        amplitude,
        max_rows=max_rows,
        max_subcarriers=max_subcarriers,
    )
    validate_amplitude_for_family(
        model.family,
        array,
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

    sample_index = idx
    sample_count = total

    return {
        "activity": activity,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "environment_id": environment_id,
        "latency_ms": round(latency_ms, 3),
        "source": replay_source,
        "presence": presence,
        "probabilities": probabilities,
        "model_version": model.version_label,
        "spatial": simulated_spatial(progress, activity),
        "sample_index": sample_index,
        "sample_count": sample_count,
    }
