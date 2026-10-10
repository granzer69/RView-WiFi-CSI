"""Replay ESP-Fi trials via load_window()."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from datasets.esp_fi import SCENARIO_NAMES, discover_trials, load_window
from simulator.sources.base import CsiStreamFrame


def session_meta_from_window_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    scenario_name = metadata.get("scenario_name") or SCENARIO_NAMES.get(
        int(metadata.get("scenario_id", 0)), "unknown"
    )
    return {
        "session_id": metadata["session_id"],
        "environment_id": str(scenario_name),
        "scenario_id": metadata["scenario_id"],
        "scenario_name": metadata.get("scenario_name"),
        "participant_id": metadata["participant_id"],
        "trial_id": metadata["trial_id"],
        "activity_code": metadata["activity_code"],
        "normalized_label": metadata["normalized_label"],
        "dataset_label": metadata["dataset_label"],
        "label_verified_by_folder": metadata["label_verified_by_folder"],
        "data_tier": "real",
        "dataset_id": metadata.get("dataset_id"),
        "dataset_version": metadata.get("dataset_version"),
    }


class DatasetReplaySource:
    """Emit one matrix row per read_next() from a loaded CsiWindow."""

    id = "dataset_replay"
    capabilities: dict[str, Any] = {
        "source": "dataset_replay",
        "dataset": "esp-fi-har",
        "frame_mode": "index",
        "phase": False,
    }

    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root
        self._records_by_id: dict[str, Any] = {}
        self._amplitude: np.ndarray | None = None
        self._meta: dict[str, Any] | None = None
        self._index = 0
        self._session_id: str | None = None

    def _ensure_catalog(self) -> None:
        if self._records_by_id:
            return
        records = discover_trials(self._data_root)
        self._records_by_id = {record.session_id: record for record in records}

    def open(self, session_id: str) -> None:
        self._ensure_catalog()
        record = self._records_by_id.get(session_id)
        if record is None:
            raise KeyError(f"unknown session_id: {session_id}")
        window = load_window(record)
        self._amplitude = np.asarray(window.amplitude, dtype=np.float64)
        self._meta = session_meta_from_window_metadata(window.metadata)
        self._index = 0
        self._session_id = session_id

    def read_next(self) -> CsiStreamFrame | None:
        if self._amplitude is None or self._meta is None:
            return None
        if self._index >= self._amplitude.shape[0]:
            return None
        row = self._amplitude[self._index]
        frame = CsiStreamFrame(
            time_index=self._index,
            subcarriers=row.tolist(),
            meta=dict(self._meta),
        )
        self._index += 1
        return frame

    def close(self) -> None:
        self._amplitude = None
        self._meta = None
        self._index = 0
        self._session_id = None

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def frame_count(self) -> int:
        if self._amplitude is None:
            return 0
        return int(self._amplitude.shape[0])
