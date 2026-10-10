"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from api.config import ApiSettings, settings
from api.inference import predict_from_amplitude
from api.model_registry import ModelRegistry
from api.replay_stream import ReplayStreamSession
from api.schemas import (
    HealthResponse,
    ModelInfo,
    ModelsResponse,
    PredictRequest,
    PredictionResponse,
)
from common.errors import DatasetError

_registry = ModelRegistry(settings)


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
        if loaded is not None:
            path = str(loaded.artifact_dir)
        else:
            try:
                path = str(registry.load_default().artifact_dir)
                loaded = registry.active()
            except FileNotFoundError:
                loaded = None
        return HealthResponse(
            model_loaded=loaded is not None,
            model_path=path,
        )

    @application.get("/models", response_model=ModelsResponse)
    def list_models() -> ModelsResponse:
        try:
            active = registry.load_default()
        except FileNotFoundError:
            active = None
        models = [
            ModelInfo(
                model_id=item.model_id,
                model_type=item.model_type,
                artifact_dir=str(item.artifact_dir),
                label_names=item.label_names,
                metrics=item.metrics,
            )
            for item in registry.list_models()
        ]
        return ModelsResponse(
            active_model_id=active.model_id if active else None,
            models=models,
        )

    @application.post("/predict", response_model=PredictionResponse)
    def predict(body: PredictRequest) -> PredictionResponse:
        try:
            model = registry.load_default()
        except FileNotFoundError as exc:
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
