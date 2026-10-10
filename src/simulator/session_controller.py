"""Transport state machine for dataset replay."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Literal

from simulator.clock import ReplayClock
from simulator.sources.base import CsiStreamFrame, CsiStreamSource

TransportAction = Literal["play", "pause", "stop", "restart"]


class TransportState(str, Enum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETE = "complete"


@dataclass
class SessionController:
    source: CsiStreamSource
    clock: ReplayClock = field(default_factory=ReplayClock)
    state: TransportState = TransportState.IDLE
    on_frame: Callable[[CsiStreamFrame], None] | None = None
    on_session_ended: Callable[[str], None] | None = None

    def open_session(self, session_id: str) -> None:
        self.source.open(session_id)
        self.clock.reset()
        self.state = TransportState.PAUSED

    def control(self, action: TransportAction, speed: float | None = None) -> TransportState:
        if speed is not None:
            self.clock.set_speed(speed)
        if action == "play":
            if self.source.session_id is None:
                raise RuntimeError("no session open")
            self.state = TransportState.PLAYING
        elif action == "pause":
            self.state = TransportState.PAUSED
        elif action == "stop":
            self.state = TransportState.STOPPED
            if self.on_session_ended:
                self.on_session_ended("stop")
        elif action == "restart":
            if self.source.session_id is None:
                raise RuntimeError("no session open")
            sid = self.source.session_id
            self.source.open(sid)
            self.clock.reset()
            self.state = TransportState.PAUSED
        return self.state

    def tick(self) -> CsiStreamFrame | None:
        if self.state != TransportState.PLAYING:
            return None
        frame = self.source.read_next()
        if frame is None:
            self.state = TransportState.COMPLETE
            if self.on_session_ended:
                self.on_session_ended("complete")
            return None
        self.clock.advance()
        if self.on_frame:
            self.on_frame(frame)
        return frame
