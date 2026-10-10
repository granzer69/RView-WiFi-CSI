"""Load and describe inference artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from api.config import ApiSettings
from models.rf import RandomForestHarModel


@dataclass
class LoadedModel:
    model_id: str
    artifact_dir: Path
    rf: RandomForestHarModel
    metrics: dict[str, Any] | None

    @property
    def model_type(self) -> str:
        return str(self.rf.config.get("model_type", "random_forest"))

    @property
    def label_names(self) -> list[str]:
        return list(self.rf.label_names)

    @property
    def version_label(self) -> str:
        return f"{self.model_type}@{self.model_id}"


class ModelRegistry:
    def __init__(self, settings: ApiSettings) -> None:
        self._settings = settings
        self._active: LoadedModel | None = None

    def load_default(self) -> LoadedModel:
        if self._active is not None:
            return self._active
        artifact_dir = self._settings.model_artifact_dir
        if not artifact_dir.is_dir():
            raise FileNotFoundError(f"model artifact directory not found: {artifact_dir}")
        run_id = artifact_dir.parent.name if artifact_dir.name in {
            "in_domain",
            "cross_user",
            "cross_environment",
        } else artifact_dir.name
        metrics_path = artifact_dir / "metrics.json"
        metrics = json.loads(metrics_path.read_text()) if metrics_path.is_file() else None
        rf = RandomForestHarModel.load(artifact_dir)
        self._active = LoadedModel(
            model_id=f"v2_rf_{artifact_dir.name}_{run_id}",
            artifact_dir=artifact_dir,
            rf=rf,
            metrics=metrics,
        )
        return self._active

    def active(self) -> LoadedModel | None:
        return self._active

    def list_models(self) -> list[LoadedModel]:
        models: list[LoadedModel] = []
        rf_root = self._settings.repo_root / "artifacts" / "v2_rf"
        if not rf_root.is_dir():
            return models
        for run_dir in sorted(rf_root.iterdir()):
            if not run_dir.is_dir():
                continue
            for strategy in ("in_domain", "cross_user", "cross_environment"):
                candidate = run_dir / strategy
                if not (candidate / "classifier.joblib").is_file():
                    continue
                metrics_path = candidate / "metrics.json"
                metrics = json.loads(metrics_path.read_text()) if metrics_path.is_file() else None
                models.append(
                    LoadedModel(
                        model_id=f"v2_rf_{strategy}_{run_dir.name}",
                        artifact_dir=candidate,
                        rf=RandomForestHarModel.load(candidate),
                        metrics=metrics,
                    )
                )
        return models
