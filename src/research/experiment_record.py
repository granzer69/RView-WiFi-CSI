"""Structured experiment provenance for research lab exports."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    complete = "complete"
    partial = "partial"
    blocked = "blocked"
    failed = "failed"


class ExperimentRecord(BaseModel):
    """JSON-serializable run metadata for research exports."""

    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    git_sha: str | None = None
    split_strategy: str
    assignment_sha256: str | None = None
    artifact_path: str
    family: str
    status: ExperimentStatus = ExperimentStatus.complete
    notes: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        payload["status"] = self.status.value
        return payload
