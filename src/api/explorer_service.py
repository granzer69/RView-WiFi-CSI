"""CSI Explorer: catalog, amplitude slices, statistics, trial-level predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from api.inference import predict_from_amplitude
from api.model_registry import ModelRegistry
from common.errors import DatasetError
from datasets.esp_fi import (
    SCENARIO_NAMES,
    SUBCARRIERS,
    TIME_STEPS,
    discover_trials,
    load_window,
)
from datasets.esp_fi import TrialRecord


def _find_record(data_root: Path, session_id: str) -> TrialRecord:
    target = session_id.strip()
    for record in discover_trials(data_root):
        if record.session_id == target:
            return record
    raise DatasetError(f"session not found: {target}")


def build_catalog(data_root: Path) -> dict[str, Any]:
    if not data_root.is_dir():
        raise DatasetError(f"ESP-Fi data root not found: {data_root}")
    records = discover_trials(data_root)
    trials = []
    for record in sorted(records, key=lambda r: r.session_id):
        trials.append(_trial_summary(record))
    return {
        "dataset_id": "esp-fi-har",
        "trial_count": len(trials),
        "shape": {"time_steps": TIME_STEPS, "subcarriers": SUBCARRIERS},
        "orientation_note": (
            "Amplitude matrices are (time_steps=950, subcarriers=52). "
            "Heatmaps plot subcarrier on the vertical axis and sample index on the horizontal axis "
            "(matplotlib imshow on amplitude.T, origin lower)."
        ),
        "label_caveat": (
            "Scenarios 1, 2, and 4 have no class folders; labels follow the scenario-3 folder map "
            "(INFERRED — NOT INDEPENDENTLY VERIFIED)."
        ),
        "trials": trials,
    }


def _trial_summary(record: TrialRecord) -> dict[str, Any]:
    return {
        "session_id": record.session_id,
        "scenario_id": record.scenario_id,
        "scenario_name": SCENARIO_NAMES[record.scenario_id],
        "participant_id": record.participant_id,
        "activity_code": record.activity_code,
        "dataset_label": record.dataset_label,
        "normalized_label": record.normalized_label,
        "trial_id": record.trial_id,
        "label_verified_by_folder": record.label_verified_by_folder,
        "label_status": "verified" if record.label_verified_by_folder else "inferred",
    }


def trial_detail(data_root: Path, session_id: str) -> dict[str, Any]:
    record = _find_record(data_root, session_id)
    window = load_window(record)
    stats = signal_statistics(window.amplitude)
    return {
        **_trial_summary(record),
        "path": record.path,
        "amplitude_transposed_on_load": bool(window.metadata.get("amplitude_transposed")),
        "statistics": stats,
    }


def signal_statistics(amplitude: np.ndarray) -> dict[str, Any]:
    array = np.asarray(amplitude, dtype=np.float64)
    if array.size == 0:
        return {
            "empty": True,
            "finite_fraction": 0.0,
            "constant": True,
        }
    finite_mask = np.isfinite(array)
    finite_fraction = float(finite_mask.mean())
    values = array[finite_mask]
    if values.size == 0:
        return {
            "empty": True,
            "finite_fraction": finite_fraction,
            "constant": True,
        }
    std = float(values.std())
    return {
        "empty": False,
        "finite_fraction": finite_fraction,
        "constant": std == 0.0,
        "mean": float(values.mean()),
        "std": std,
        "min": float(values.min()),
        "max": float(values.max()),
        "shape": [int(array.shape[0]), int(array.shape[1])],
    }


def slice_amplitude(
    data_root: Path,
    session_id: str,
    *,
    row_start: int = 0,
    row_end: int | None = None,
    max_rows: int = 950,
    subcarrier_start: int = 0,
    subcarrier_end: int | None = None,
) -> dict[str, Any]:
    record = _find_record(data_root, session_id)
    window = load_window(record)
    matrix = window.amplitude
    n_rows, n_cols = matrix.shape
    end_row = row_end if row_end is not None else n_rows
    end_row = min(end_row, n_rows)
    start_row = max(0, min(row_start, end_row))
    if end_row - start_row > max_rows:
        end_row = start_row + max_rows
    sc_end = subcarrier_end if subcarrier_end is not None else n_cols
    sc_end = min(sc_end, n_cols)
    sc_start = max(0, min(subcarrier_start, sc_end))
    block = matrix[start_row:end_row, sc_start:sc_end]
    return {
        "session_id": session_id,
        "kind": "raw_amplitude",
        "row_start": start_row,
        "row_end": end_row,
        "subcarrier_start": sc_start,
        "subcarrier_end": sc_end,
        "shape": [int(block.shape[0]), int(block.shape[1])],
        "amplitude": block.tolist(),
    }


def subcarrier_waveform(
    data_root: Path,
    session_id: str,
    subcarrier_index: int,
) -> dict[str, Any]:
    if subcarrier_index < 0 or subcarrier_index >= SUBCARRIERS:
        raise DatasetError(f"subcarrier_index must be in 0..{SUBCARRIERS - 1}")
    record = _find_record(data_root, session_id)
    window = load_window(record)
    trace = window.amplitude[:, subcarrier_index]
    return {
        "session_id": session_id,
        "kind": "raw_amplitude_trace",
        "subcarrier_index": subcarrier_index,
        "sample_indices": list(range(trace.shape[0])),
        "values": trace.tolist(),
        "ground_truth_label": record.normalized_label,
    }


def compare_trials(data_root: Path, session_a: str, session_b: str) -> dict[str, Any]:
    a = trial_detail(data_root, session_a)
    b = trial_detail(data_root, session_b)
    stats_a = a["statistics"]
    stats_b = b["statistics"]
    shared_scale = None
    if not stats_a.get("empty") and not stats_b.get("empty"):
        shared_scale = {
            "min": min(stats_a["min"], stats_b["min"]),
            "max": max(stats_a["max"], stats_b["max"]),
        }
    return {
        "session_a": session_a,
        "session_b": session_b,
        "trial_a": a,
        "trial_b": b,
        "compatible_scales": shared_scale,
        "same_participant": a["participant_id"] == b["participant_id"],
        "same_scenario": a["scenario_id"] == b["scenario_id"],
        "same_ground_truth": a["normalized_label"] == b["normalized_label"],
    }


def trial_prediction(
    data_root: Path,
    registry: ModelRegistry,
    session_id: str,
    *,
    model_id: str | None,
    max_rows: int,
    max_subcarriers: int,
) -> dict[str, Any]:
    record = _find_record(data_root, session_id)
    window = load_window(record)
    if model_id:
        model = registry.load_by_id(model_id)
    else:
        model = registry.load_default()
    amplitude = window.amplitude.tolist()
    payload = predict_from_amplitude(
        model,
        amplitude,
        session_id=record.session_id,
        environment_id=SCENARIO_NAMES[record.scenario_id],
        time_index=window.n_times - 1,
        frame_count=window.n_times,
        max_rows=max_rows,
        max_subcarriers=max_subcarriers,
    )
    return {
        "session_id": session_id,
        "ground_truth_label": record.normalized_label,
        "dataset_label": record.dataset_label,
        "label_verified_by_folder": record.label_verified_by_folder,
        "model_id": model.model_id,
        "prediction": payload,
        "alignment": "trial_level",
        "note": "One prediction per trial using the full amplitude matrix (950×52).",
    }

