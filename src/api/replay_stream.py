"""WebSocket dataset replay with model predictions."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from api.config import ApiSettings
from api.inference import predict_from_amplitude
from api.model_registry import ModelRegistry
from simulator.sources.dataset_replay import DatasetReplaySource


class ReplayStreamSession:
    def __init__(
        self,
        websocket: WebSocket,
        settings: ApiSettings,
        registry: ModelRegistry,
    ) -> None:
        self._websocket = websocket
        self._settings = settings
        self._registry = registry
        self._source = DatasetReplaySource(settings.data_root)
        self._task: asyncio.Task[None] | None = None
        self._playing = False
        self._speed = 1.0
        self._buffer: list[list[float]] = []
        self._frame_count = 0
        self._meta: dict[str, Any] | None = None

    async def run(self) -> None:
        await self._websocket.accept()
        try:
            while True:
                message = await self._websocket.receive_text()
                await self._handle(json.loads(message))
        except WebSocketDisconnect:
            await self._stop_loop()
        except asyncio.CancelledError:
            await self._stop_loop()
            raise

    async def _handle(self, payload: dict[str, Any]) -> None:
        msg_type = payload.get("type")
        if msg_type == "open_session":
            session_id = str(payload.get("session_id", ""))
            if not session_id:
                await self._send_error("session_id is required")
                return
            await self._open_session(session_id)
        elif msg_type == "control":
            await self._control(str(payload.get("action", "")), payload.get("speed"))
        elif msg_type == "ping":
            await self._websocket.send_json({"type": "pong"})
        else:
            await self._send_error(f"unknown message type: {msg_type}")

    async def _open_session(self, session_id: str) -> None:
        await self._stop_loop()
        try:
            self._source.open(session_id)
        except KeyError:
            await self._send_error(f"unknown session_id: {session_id}")
            return
        self._buffer = []
        self._frame_count = self._source.frame_count
        self._meta = None
        await self._websocket.send_json(
            {
                "type": "session_started",
                "session_id": session_id,
                "source": "dataset_replay",
            }
        )

    async def _control(self, action: str, speed: float | None) -> None:
        if speed is not None:
            self._speed = float(speed)
        if action == "play":
            if self._source.session_id is None:
                await self._send_error("no session open")
                return
            self._playing = True
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._replay_loop())
        elif action == "pause":
            self._playing = False
        elif action == "stop":
            await self._stop_loop()
            self._source.close()
            await self._websocket.send_json({"type": "session_ended", "reason": "stop"})
        elif action == "restart":
            await self._stop_loop()
            sid = self._source.session_id
            if sid:
                self._source.open(sid)
                self._buffer = []
                self._frame_count = self._source.frame_count
                await self._emit_frame_at(0)
        else:
            await self._send_error(f"unknown control action: {action}")

    async def _stop_loop(self) -> None:
        self._playing = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _replay_loop(self) -> None:
        interval = 1.0 / (self._settings.nominal_replay_hz * max(self._speed, 0.1))
        try:
            while self._playing:
                frame = self._source.read_next()
                if frame is None:
                    self._playing = False
                    await self._websocket.send_json({"type": "session_ended", "reason": "complete"})
                    break
                self._meta = frame.meta
                self._buffer.append(frame.subcarriers)
                await self._websocket.send_json(
                    {
                        "type": "csi_frame",
                        "time_index": frame.time_index,
                        "subcarriers": frame.subcarriers,
                        "meta": frame.meta,
                    }
                )
                await self._emit_prediction(frame.time_index)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    async def _emit_frame_at(self, time_index: int) -> None:
        if self._source.session_id is None:
            return
        self._source.open(self._source.session_id)
        self._buffer = []
        for _ in range(time_index + 1):
            frame = self._source.read_next()
            if frame is None:
                break
            self._buffer.append(frame.subcarriers)
            self._meta = frame.meta
        if self._meta is None:
            return
        await self._websocket.send_json(
            {
                "type": "csi_frame",
                "time_index": time_index,
                "subcarriers": self._buffer[-1],
                "meta": self._meta,
            }
        )
        await self._emit_prediction(time_index)

    async def _emit_prediction(self, time_index: int) -> None:
        if self._meta is None or not self._buffer:
            return
        model = self._registry.load_default()
        prediction = predict_from_amplitude(
            model,
            self._buffer,
            session_id=str(self._meta.get("session_id", "")),
            environment_id=str(self._meta.get("environment_id", "")),
            time_index=time_index,
            frame_count=self._frame_count,
            max_rows=self._settings.max_amplitude_rows,
            max_subcarriers=self._settings.max_subcarriers,
        )
        prediction["source"] = "dataset_replay"
        await self._websocket.send_json({"type": "prediction", "payload": prediction})

    async def _send_error(self, message: str) -> None:
        await self._websocket.send_json({"type": "error", "message": message})
