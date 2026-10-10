"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = "v3"
    model_loaded: bool
    model_path: str | None = None
    active_model_id: str | None = None
    model_load_error: str | None = None


class ModelInfo(BaseModel):
    model_id: str
    model_type: str
    family: str
    split_strategy: str
    run_id: str
    artifact_dir: str
    label_names: list[str]
    metrics: dict[str, Any] | None = None
    load_error: str | None = None


class ModelsResponse(BaseModel):
    active_model_id: str | None
    models: list[ModelInfo]


class SelectModelRequest(BaseModel):
    model_id: str


class PredictRequest(BaseModel):
    amplitude: list[list[float]] = Field(
        ...,
        description="Time-major CSI amplitude (rows <= 950, cols == 52)",
    )
    session_id: str | None = None
    environment_id: str | None = None
    time_index: int | None = None
    frame_count: int | None = None

    @field_validator("amplitude")
    @classmethod
    def non_empty(cls, value: list[list[float]]) -> list[list[float]]:
        if not value:
            raise ValueError("amplitude must contain at least one row")
        return value


class PredictionResponse(BaseModel):
    activity: str
    confidence: float
    timestamp: str
    session_id: str
    environment_id: str
    latency_ms: float
    source: Literal["model", "dataset_replay"] = "model"
    presence: bool = True
    probabilities: dict[str, float] | None = None
    model_version: str | None = None
    spatial: dict[str, Any] | None = None
