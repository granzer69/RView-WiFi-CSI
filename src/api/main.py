"""FastAPI application entrypoint."""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from api.config import ApiSettings, settings
from api.inference import predict_from_amplitude
from api.model_registry import ModelRegistry
from api.replay_manifest import build_manifest
from api.replay_stream import ReplayStreamSession
from api.schemas import (
    HealthResponse,
    ModelInfo,
    ModelsResponse,
    PredictRequest,
    PredictionResponse,
    SelectModelRequest,
)
from common.errors import DatasetError

_registry = ModelRegistry(settings)


def _resolve_active(registry: ModelRegistry, cfg: ApiSettings):
    if cfg.active_model_id:
        try:
            return registry.load_by_id(cfg.active_model_id)
        except FileNotFoundError:
            pass
    return registry.load_default()


def create_app(api_settings: ApiSettings | None = None) -> FastAPI:
    cfg = api_settings or settings
    registry = ModelRegistry(cfg)
    application = FastAPI(title="R-View WiFi CSI Platform", version="0.3.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        loaded = registry.active()
        path: str | None = None
        load_error = registry.last_load_error()
        try:
            if loaded is None:
                loaded = _resolve_active(registry, cfg)
            path = str(loaded.artifact_dir)
        except FileNotFoundError as exc:
            loaded = None
            load_error = str(exc)
        return HealthResponse(
            model_loaded=loaded is not None,
            model_path=path,
            active_model_id=registry.active_model_id(),
            model_load_error=load_error,
        )

    @application.get("/models", response_model=ModelsResponse)
    def list_models() -> ModelsResponse:
        active_id = registry.active_model_id()
        try:
            active = _resolve_active(registry, cfg)
            active_id = active.model_id
        except FileNotFoundError:
            active_id = active_id or cfg.active_model_id
        models = [
            ModelInfo(
                model_id=item["model_id"],
                model_type=item["model_type"],
                family=item["family"],
                split_strategy=item["split_strategy"],
                run_id=item["run_id"],
                artifact_dir=item["artifact_dir"],
                label_names=item["label_names"],
                metrics=item.get("metrics"),
                load_error=item.get("load_error"),
            )
            for item in registry.list_model_descriptors()
        ]
        return ModelsResponse(active_model_id=active_id, models=models)

    @application.put("/models/active", response_model=ModelsResponse)
    def select_active_model(body: SelectModelRequest) -> ModelsResponse:
        try:
            registry.load_by_id(body.model_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return list_models()

    def _read_research_json(filename: str) -> dict:
        path = cfg.repo_root / "frontend" / "public" / "research" / filename
        if not path.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"Research export missing: {path}. Run scripts/export_research_lab.py",
            )
        return json.loads(path.read_text(encoding="utf-8"))

    @application.get("/research/generalization")
    def research_generalization() -> dict:
        return _read_research_json("generalization.json")

    @application.get("/research/participants")
    def research_participants() -> dict:
        return _read_research_json("participants.json")

    @application.get("/replay/manifest")
    def replay_manifest() -> dict:
        if not cfg.data_root.is_dir():
            raise HTTPException(
                status_code=404,
                detail=f"ESP-Fi data root not found: {cfg.data_root}",
            )
        return build_manifest(cfg.data_root, nominal_replay_hz=cfg.nominal_replay_hz)

    @application.post("/predict", response_model=PredictionResponse)
    def predict(body: PredictRequest) -> PredictionResponse:
        try:
            model = _resolve_active(registry, cfg)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        session_id = body.session_id or "unknown"
        environment_id = body.environment_id or "unknown"
        try:
            payload = predict_from_amplitude(
                model,
                body.amplitude,
                session_id=session_id,
                environment_id=environment_id,
                time_index=body.time_index,
                frame_count=body.frame_count,
                max_rows=cfg.max_amplitude_rows,
                max_subcarriers=cfg.max_subcarriers,
            )
        except DatasetError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return PredictionResponse(**payload)

    @application.websocket("/ws/stream")
    async def stream(websocket: WebSocket) -> None:
        session = ReplayStreamSession(websocket, cfg, registry)
        await session.run()

    return application


app = create_app()
