"""Replay clock: nominal Hz scaled by transport speed."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_NOMINAL_REPLAY_HZ = 95.0
ALLOWED_SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


@dataclass
class ReplayClock:
    """Index-based replay timing (not verified MAT capture clock)."""

    nominal_hz: float = DEFAULT_NOMINAL_REPLAY_HZ
    speed: float = 1.0
    time_index: int = 0

    def __post_init__(self) -> None:
        if self.nominal_hz <= 0:
            raise ValueError("nominal_hz must be positive")
        self.set_speed(self.speed)

    def set_speed(self, speed: float) -> None:
        if speed not in ALLOWED_SPEEDS:
            raise ValueError(f"speed must be one of {ALLOWED_SPEEDS}, got {speed}")
        self.speed = speed

    @property
    def tick_interval_seconds(self) -> float:
        return 1.0 / (self.nominal_hz * self.speed)

    def reset(self) -> None:
        self.time_index = 0

    def advance(self) -> int:
        self.time_index += 1
        return self.time_index
