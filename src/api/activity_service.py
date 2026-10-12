"""On-demand trial / sample evaluation for the Activity workbench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from api.inference import predict_from_amplitude, resolve_active_model
from api.model_registry import ModelRegistry
from common.errors import DatasetError
from datasets.esp_fi import SCENARIO_NAMES, discover_trials, load_window


def list_activity_trials(data_root: Path) -> dict[str, Any]:
    if not data_root.is_dir():
        raise DatasetError(f"ESP-Fi data root not found: {data_root}")
    trials = []
    for record in sorted(discover_trials(data_root), key=lambda r: r.session_id):
        trials.append(
            {
                "session_id": record.session_id,
                "participant_id": record.participant_id,
                "scenario_id": record.scenario_id,
                "normalized_label": record.normalized_label,
                "label_verified_by_folder": record.label_verified_by_folder,
            }
        )
    return {"dataset_id": "esp-fi-har", "trial_count": len(trials), "trials": trials}


def evaluate_trial_sample(
    data_root: Path,
    registry: ModelRegistry,
    settings: Any,
    *,
    session_id: str,
    sample_index: int,
    model_id: str | None = None,
) -> dict[str, Any]:
    target = session_id.strip()
    record = None
    for item in discover_trials(data_root):
        if item.session_id == target:
            record = item
            break
    if record is None:
        raise DatasetError(f"session not found: {target}")
    window = load_window(record)
    n_times = window.n_times
    if sample_index < 0 or sample_index >= n_times:
        raise DatasetError(f"sample_index must be in 0..{n_times - 1}")
    prefix = window.amplitude[: sample_index + 1]
    model = resolve_active_model(registry, settings, model_id=model_id)
    try:
        prediction = predict_from_amplitude(
            model,
            prefix.tolist(),
            session_id=record.session_id,
            environment_id=SCENARIO_NAMES[record.scenario_id],
            time_index=sample_index,
            frame_count=n_times,
            max_rows=settings.max_amplitude_rows,
            max_subcarriers=settings.max_subcarriers,
            replay_source="dataset_replay",
        )
    except DatasetError as exc:
        return {
            "session_id": record.session_id,
            "sample_index": sample_index,
            "sample_count": n_times,
            "ground_truth_label": record.normalized_label,
            "model_id": model.model_id,
            "status": "error",
            "error": str(exc),
        }
    pred_label = prediction["activity"]
    gt = record.normalized_label
    if pred_label == gt:
        eval_status = "evaluated-correct"
    else:
        eval_status = "evaluated-incorrect"
    return {
        "session_id": record.session_id,
        "sample_index": sample_index,
        "sample_count": n_times,
        "ground_truth_label": gt,
        "model_id": model.model_id,
        "status": eval_status,
        "prediction": prediction,
    }
