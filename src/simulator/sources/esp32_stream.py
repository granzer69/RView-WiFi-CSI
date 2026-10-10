"""V4 placeholder — hardware stream not implemented."""

from __future__ import annotations

from typing import Any

from simulator.sources.base import CsiStreamFrame


class ESP32CSIStreamSource:
    id = "esp32_stream"
    capabilities: dict[str, Any] = {"source": "esp32_stream", "implemented": False}

    def open(self, session_id: str) -> None:
        raise NotImplementedError("ESP32 CSI stream is V4 only")

    def read_next(self) -> CsiStreamFrame | None:
        return None

    def close(self) -> None:
        pass

    @property
    def session_id(self) -> str | None:
        return None

    @property
    def frame_count(self) -> int:
        return 0
