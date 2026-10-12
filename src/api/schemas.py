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


class SourceStatusResponse(BaseModel):
    mode: Literal["dataset_replay", "live_unavailable"]
    reason: str
    dataset_id: str | None = None
    live_implemented: bool = False


class ActivitySampleRequest(BaseModel):
    session_id: str
    sample_index: int = Field(ge=0)
    model_id: str | None = None


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
    sample_index: int | None = None
    sample_count: int | None = None


class ExplorerCatalogResponse(BaseModel):
    dataset_id: str
    trial_count: int
    shape: dict[str, int]
    orientation_note: str
    label_caveat: str
    trials: list[dict[str, Any]]


class AmplitudeSliceResponse(BaseModel):
    session_id: str
    kind: str
    row_start: int
    row_end: int
    subcarrier_start: int
    subcarrier_end: int
    shape: list[int]
    amplitude: list[list[float]]


class ExperimentRunRequest(BaseModel):
    family: Literal["logreg", "rf", "cnn1d", "gru"]
    strategies: list[Literal["in_domain", "cross_user", "cross_environment"]] | None = None
    seed: int = 42
    preprocess: dict[str, Any] | None = None
    model: dict[str, Any] | None = None
    run_id: str | None = None
    name: str | None = None
    verify_assignment_hash: bool = True
    dataset_root: str | None = None
    preview_only: bool = False


class ExperimentRunResponse(BaseModel):
    run_id: str
    family: str
    status: str
    artifacts_dir: str | None = None
    preview: dict[str, Any] | None = None
