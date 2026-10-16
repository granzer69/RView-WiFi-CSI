"""WebSocket dataset replay with model predictions."""

from __future__ import annotations

import asyncio
import json
from collections import deque
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from api.config import ApiSettings
from api.inference import predict_from_amplitude, resolve_active_model
from api.model_registry import ModelRegistry
from simulator.clock import ALLOWED_SPEEDS, ReplayClock
from simulator.session_controller import SessionController, TransportState
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
        self._clock = ReplayClock()
        self._controller = SessionController(source=self._source, clock=self._clock)
        self._task: asyncio.Task[None] | None = None
        self._buffer: deque[list[float]] = deque(maxlen=settings.ws_replay_buffer_rows)
        self._history: list[dict[str, Any]] = []
        self._history_limit = 200
        self._session_meta: dict[str, Any] | None = None
        self._speed = 1.0

    async def run(self) -> None:
        await self._websocket.accept()
        await self._emit_model_status()
        try:
            while True:
                message = await self._websocket.receive_text()
                await self._handle(json.loads(message))
        except WebSocketDisconnect:
            await self._stop_loop()
        except asyncio.CancelledError:
            await self._stop_loop()
            raise

    async def _emit_model_status(self) -> None:
        loaded = self._registry.active()
        load_error = self._registry.last_load_error()
        model_id = self._registry.active_model_id()
        if loaded is None:
            try:
                loaded = resolve_active_model(self._registry, self._settings)
                model_id = loaded.model_id
            except Exception as exc:  # noqa: BLE001
                load_error = str(exc)
                loaded = None
        await self._websocket.send_json(
            {
                "type": "model_status",
                "model_loaded": loaded is not None,
                "active_model_id": model_id,
                "model_version": loaded.version_label if loaded else None,
                "load_error": load_error,
            }
        )

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
        elif msg_type == "select_model":
            model_id = str(payload.get("model_id", ""))
            if not model_id:
                await self._send_error("model_id is required")
                return
            try:
                self._registry.load_by_id(model_id)
            except Exception as exc:  # noqa: BLE001
                await self._send_error(f"model load failed: {exc}")
                return
            await self._emit_model_status()
        elif msg_type == "ping":
            await self._websocket.send_json({"type": "pong"})
        else:
            await self._send_error(f"unknown message type: {msg_type}")

    async def _open_session(self, session_id: str) -> None:
        await self._stop_loop()
        if not self._settings.data_root.is_dir():
            await self._send_error(
                f"ESP-Fi data root missing: {self._settings.data_root}. "
                "Set RVIEW_DATA_ROOT or export trials for local replay."
            )
            return
        try:
            self._controller.open_session(session_id)
        except KeyError:
            await self._send_error(f"unknown session_id: {session_id}")
            return
        self._buffer.clear()
        self._history.clear()
        self._session_meta = None
        frame_count = self._source.frame_count
        await self._websocket.send_json(
            {
                "type": "session_started",
                "session_id": session_id,
                "source": "dataset_replay",
                "frame_count": frame_count,
                "sample_count": frame_count,
            }
        )

    async def _control(self, action: str, speed: float | None) -> None:
        clock_speed = None
        if speed is not None:
            self._speed = float(speed)
            if self._speed in ALLOWED_SPEEDS:
                clock_speed = self._speed
        try:
            state = self._controller.control(action, speed=clock_speed)  # type: ignore[arg-type]
        except RuntimeError as exc:
            await self._send_error(str(exc))
            return
        if action == "play":
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._replay_loop())
        elif action == "stop":
            await self._stop_loop()
            self._source.close()
            await self._websocket.send_json({"type": "session_ended", "reason": "stop"})
        elif action == "restart":
            await self._stop_loop()
            self._buffer.clear()
            self._history.clear()
            if self._source.session_id:
                idx = 0
                await self._emit_frame_at(idx)
        if action in ("play", "pause", "restart"):
            await self._websocket.send_json(
                {"type": "transport_state", "state": state.value, "speed": self._clock.speed}
            )

    async def _stop_loop(self) -> None:
        if self._controller.state == TransportState.PLAYING:
            self._controller.control("pause")
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def _append_row(self, row: list[float]) -> None:
        self._buffer.append(row)

    async def _replay_loop(self) -> None:
        interval = 1.0 / (self._settings.nominal_replay_hz * max(self._speed, 0.1))
        try:
            while self._controller.state == TransportState.PLAYING:
                frame = self._controller.tick()
                if frame is None:
                    if self._controller.state == TransportState.COMPLETE:
                        await self._websocket.send_json(
                            {"type": "session_ended", "reason": "complete"}
                        )
                    break
                self._append_row(frame.subcarriers)
                self._session_meta = frame.meta
                sample_index = frame.time_index
                sample_count = self._source.frame_count
                await self._websocket.send_json(
                    {
                        "type": "csi_frame",
                        "time_index": sample_index,
                        "sample_index": sample_index,
                        "sample_count": sample_count,
                        "subcarriers": frame.subcarriers,
                        "meta": frame.meta,
                        "source": "dataset_replay",
                    }
                )
                await self._emit_prediction(sample_index, sample_count)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    async def _emit_frame_at(self, time_index: int) -> None:
        if self._source.session_id is None:
            return
        self._source.open(self._source.session_id)
        self._buffer.clear()
        for _ in range(time_index + 1):
            frame = self._source.read_next()
            if frame is None:
                break
            self._append_row(frame.subcarriers)
            self._session_meta = frame.meta
        if not self._buffer:
            return
        sample_count = self._source.frame_count
        await self._websocket.send_json(
            {
                "type": "csi_frame",
                "time_index": time_index,
                "sample_index": time_index,
                "sample_count": sample_count,
                "subcarriers": self._buffer[-1],
                "meta": self._session_meta,
                "source": "dataset_replay",
            }
        )
        await self._emit_prediction(time_index, sample_count)

    async def _emit_prediction(self, sample_index: int, sample_count: int) -> None:
        if not self._buffer or self._session_meta is None:
            return
        meta = self._session_meta
        try:
            model = resolve_active_model(self._registry, self._settings)
        except Exception as exc:  # noqa: BLE001
            await self._websocket.send_json(
                {"type": "model_status", "model_loaded": False, "load_error": str(exc)}
            )
            await self._send_error(f"model not loaded: {exc}")
            return
        try:
            prediction = predict_from_amplitude(
                model,
                list(self._buffer),
                session_id=str(meta.get("session_id", "")),
                environment_id=str(meta.get("environment_id", "")),
                time_index=sample_index,
                frame_count=sample_count,
                max_rows=self._settings.max_amplitude_rows,
                max_subcarriers=self._settings.max_subcarriers,
                replay_source="dataset_replay",
            )
        except Exception as exc:  # noqa: BLE001
            await self._send_error(f"prediction failed: {exc}")
            return
        history_item = {
            "time_index": sample_index,
            "sample_index": sample_index,
            "activity": prediction["activity"],
            "confidence": prediction["confidence"],
            "presence": prediction.get("presence", True),
        }
        self._history.append(history_item)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit :]
        await self._websocket.send_json({"type": "prediction", "payload": prediction})
        await self._websocket.send_json({"type": "timeline", "entries": self._history[-20:]})

    async def _send_error(self, message: str) -> None:
        await self._websocket.send_json({"type": "error", "message": message})
