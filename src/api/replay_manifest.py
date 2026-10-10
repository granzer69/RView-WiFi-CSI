"""Build replay manifest JSON from on-disk ESP-Fi trials."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from datasets.esp_fi import SCENARIO_NAMES, discover_trials


def build_manifest(data_root: Path, *, nominal_replay_hz: float = 95.0) -> dict[str, Any]:
    records = discover_trials(data_root)
    sessions = []
    for record in sorted(records, key=lambda r: r.session_id):
        sessions.append(
            {
                "session_id": record.session_id,
                "scenario_id": record.scenario_id,
                "scenario_name": SCENARIO_NAMES[record.scenario_id],
                "environment_id": SCENARIO_NAMES[record.scenario_id],
                "participant_id": record.participant_id,
                "activity_code": record.activity_code,
                "normalized_label": record.normalized_label,
                "dataset_label": record.dataset_label,
                "label_verified_by_folder": record.label_verified_by_folder,
            }
        )
    default_session = "1-1-2-1"
    if not any(s["session_id"] == default_session for s in sessions) and sessions:
        default_session = sessions[0]["session_id"]
    return {
        "dataset_id": "esp-fi-har",
        "source": "dataset_replay",
        "nominal_replay_hz": nominal_replay_hz,
        "timing_note": "Matrix index replay at nominal Hz — not verified MAT capture clock.",
        "session_count": len(sessions),
        "sessions": sessions,
        "default_session_id": default_session,
    }
