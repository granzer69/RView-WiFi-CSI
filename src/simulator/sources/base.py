"""Abstract CSI stream source protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class CsiStreamFrame:
    """One replay tick: a single amplitude row plus session metadata."""

    time_index: int
    subcarriers: list[float]
    meta: dict[str, Any]
    wall_timestamp_ms: int | None = None


class CsiStreamSource(Protocol):
    """Pluggable source for simulator replay (dataset or future ESP32)."""

    id: str
    capabilities: dict[str, Any]

    def open(self, session_id: str) -> None: ...

    def read_next(self) -> CsiStreamFrame | None: ...

    def close(self) -> None: ...

    @property
    def session_id(self) -> str | None: ...

    @property
    def frame_count(self) -> int: ...
