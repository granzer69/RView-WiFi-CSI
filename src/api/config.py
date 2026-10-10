"""Runtime configuration for the V3 API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ApiSettings:
    """Environment-driven API settings."""

    repo_root: Path
    data_root: Path
    model_artifact_dir: Path
    cors_origins: tuple[str, ...]
    max_amplitude_rows: int = 950
    max_subcarriers: int = 52
    nominal_replay_hz: float = 95.0

    @classmethod
    def from_env(cls) -> ApiSettings:
        root = _repo_root()
        model_dir = os.environ.get(
            "RVIEW_MODEL_DIR",
            str(root / "artifacts" / "v2_rf" / "20261010T060000Z" / "in_domain"),
        )
        data_root = os.environ.get("RVIEW_DATA_ROOT", str(root / "data" / "raw" / "esp-fi-har"))
        cors = os.environ.get("RVIEW_CORS_ORIGINS", "http://127.0.0.1:43123,http://localhost:43123")
        return cls(
            repo_root=root,
            data_root=Path(data_root),
            model_artifact_dir=Path(model_dir),
            cors_origins=tuple(part.strip() for part in cors.split(",") if part.strip()),
        )


settings = ApiSettings.from_env()
