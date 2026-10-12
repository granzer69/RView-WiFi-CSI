"""CSI source availability for V4 sensing platform."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from api.config import ApiSettings
from simulator.sources.esp32_stream import ESP32CSIStreamSource


def build_source_status(settings: ApiSettings) -> dict[str, Any]:
    data_root = settings.data_root
    if data_root.is_dir():
        return {
            "mode": "dataset_replay",
            "reason": f"ESP-Fi trials available at {data_root}",
            "dataset_id": "esp-fi-har",
            "live_implemented": False,
        }
    esp32 = ESP32CSIStreamSource()
    return {
        "mode": "live_unavailable",
        "reason": (
            f"Dataset replay root missing ({data_root}). "
            f"Hardware stream ({esp32.id}) is not implemented — {esp32.capabilities}"
        ),
        "dataset_id": None,
        "live_implemented": False,
    }
