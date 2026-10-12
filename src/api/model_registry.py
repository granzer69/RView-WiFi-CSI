"""Load and describe inference artifacts across the V2 model ladder."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from api.config import ApiSettings
from common.errors import DatasetError
from models.gbdt import GbdtHarModel
from models.logreg import LogRegHarModel
from models.mlp import MlpHarModel
from models.rf import RandomForestHarModel

STRATEGIES = ("in_domain", "cross_user", "cross_environment")

FAMILY_LOADERS: dict[str, tuple[str, ...]] = {
    "logreg": ("classifier.joblib",),
    "rf": ("classifier.joblib",),
    "mlp": ("classifier.joblib",),
    "gbdt": ("classifier.joblib",),
    "cnn1d": ("model.pt",),
    "gru": ("model.pt",),
    "tcn": ("model.pt",),
}


class HarBackend(Protocol):
    label_names: tuple[str, ...]
    config: dict[str, Any]

    def predict_proba(self, amplitudes: Any) -> Any: ...


@dataclass
class LoadedModel:
    model_id: str
    family: str
    split_strategy: str
    run_id: str
    artifact_dir: Path
    backend: HarBackend
    metrics: dict[str, Any] | None
    load_error: str | None = None

    @property
    def model_type(self) -> str:
        return str(self.backend.config.get("model_type", self.family))

    @property
    def label_names(self) -> list[str]:
        return list(self.backend.label_names)

    @property
    def version_label(self) -> str:
        return f"{self.model_type}@{self.model_id}"


def _load_backend(family: str, artifact_dir: Path) -> HarBackend:
    if family == "logreg":
        return LogRegHarModel.load(artifact_dir)
    if family == "rf":
        return RandomForestHarModel.load(artifact_dir)
    if family == "mlp":
        return MlpHarModel.load(artifact_dir)
    if family == "gbdt":
        return GbdtHarModel.load(artifact_dir)
    if family == "cnn1d":
        from models.cnn1d import Cnn1dHarModel

        return Cnn1dHarModel.load(artifact_dir)
    if family == "gru":
        from models.gru import GruHarModel

        return GruHarModel.load(artifact_dir)
    if family == "tcn":
        from models.tcn import TcnHarModel

        return TcnHarModel.load(artifact_dir)
    raise DatasetError(f"unsupported model family: {family}")


def _model_id(family: str, strategy: str, run_id: str) -> str:
    return f"v2_{family}_{strategy}_{run_id}"


def _artifact_dir_from_settings(settings: ApiSettings) -> Path:
    return settings.model_artifact_dir


def _infer_descriptor(artifact_dir: Path) -> tuple[str, str, str] | None:
    """Return (family, strategy, run_id) when path points at a strategy folder."""
    if artifact_dir.name in STRATEGIES and artifact_dir.parent.parent.name.startswith("v2_"):
        family = artifact_dir.parent.parent.name.replace("v2_", "")
        return family, artifact_dir.name, artifact_dir.parent.name
    return None


class ModelRegistry:
    def __init__(self, settings: ApiSettings) -> None:
        self._settings = settings
        self._active: LoadedModel | None = None
        self._active_id: str | None = None
        self._last_load_error: str | None = None
        if settings.active_model_id:
            try:
                self.load_by_id(settings.active_model_id)
            except Exception as exc:  # noqa: BLE001
                self._last_load_error = str(exc)

    def last_load_error(self) -> str | None:
        return self._last_load_error

    def discover_entries(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        artifacts = self._settings.repo_root / "artifacts"
        if not artifacts.is_dir():
            return entries
        for family_dir in sorted(artifacts.glob("v2_*")):
            if not family_dir.is_dir():
                continue
            family = family_dir.name.replace("v2_", "")
            if family not in FAMILY_LOADERS:
                continue
            marker = FAMILY_LOADERS[family][0]
            for run_dir in sorted(family_dir.iterdir()):
                if not run_dir.is_dir():
                    continue
                for strategy in STRATEGIES:
                    candidate = run_dir / strategy
                    if not (candidate / marker).is_file():
                        continue
                    metrics_path = candidate / "metrics.json"
                    metrics = (
                        json.loads(metrics_path.read_text())
                        if metrics_path.is_file()
                        else None
                    )
                    entries.append(
                        {
                            "model_id": _model_id(family, strategy, run_dir.name),
                            "family": family,
                            "split_strategy": strategy,
                            "run_id": run_dir.name,
                            "artifact_dir": candidate,
                            "metrics": metrics,
                        }
                    )
        return entries

    def _load_entry(self, entry: dict[str, Any]) -> LoadedModel:
        artifact_dir = Path(entry["artifact_dir"])
        family = str(entry["family"])
        try:
            backend = _load_backend(family, artifact_dir)
            load_error = None
        except Exception as exc:  # noqa: BLE001 — surface in health/UI
            self._last_load_error = str(exc)
            raise
        self._last_load_error = None
        return LoadedModel(
            model_id=str(entry["model_id"]),
            family=family,
            split_strategy=str(entry["split_strategy"]),
            run_id=str(entry["run_id"]),
            artifact_dir=artifact_dir,
            backend=backend,
            metrics=entry.get("metrics"),
        )

    def load_by_id(self, model_id: str) -> LoadedModel:
        for entry in self.discover_entries():
            if entry["model_id"] == model_id:
                loaded = self._load_entry(entry)
                self._active = loaded
                self._active_id = model_id
                return loaded
        raise FileNotFoundError(f"model not found: {model_id}")

    def load_default(self) -> LoadedModel:
        if self._active is not None:
            return self._active
        artifact_dir = _artifact_dir_from_settings(self._settings)
        if not artifact_dir.is_dir():
            raise FileNotFoundError(f"model artifact directory not found: {artifact_dir}")
        inferred = _infer_descriptor(artifact_dir)
        if inferred is not None:
            family, strategy, run_id = inferred
            model_id = _model_id(family, strategy, run_id)
            for entry in self.discover_entries():
                if entry["model_id"] == model_id:
                    loaded = self._load_entry(entry)
                    self._active = loaded
                    self._active_id = model_id
                    return loaded
        # Legacy path: RF-only folder without full discovery match
        metrics_path = artifact_dir / "metrics.json"
        metrics = json.loads(metrics_path.read_text()) if metrics_path.is_file() else None
        run_id = artifact_dir.parent.name if artifact_dir.name in STRATEGIES else artifact_dir.name
        strategy = artifact_dir.name if artifact_dir.name in STRATEGIES else "in_domain"
        family = "rf"
        try:
            backend = RandomForestHarModel.load(artifact_dir)
        except Exception as exc:  # noqa: BLE001
            self._last_load_error = str(exc)
            raise
        self._last_load_error = None
        loaded = LoadedModel(
            model_id=f"v2_rf_{strategy}_{run_id}",
            family=family,
            split_strategy=strategy,
            run_id=run_id,
            artifact_dir=artifact_dir,
            backend=backend,
            metrics=metrics,
        )
        self._active = loaded
        self._active_id = loaded.model_id
        return loaded

    def active(self) -> LoadedModel | None:
        return self._active

    def active_model_id(self) -> str | None:
        return self._active_id

    def list_model_descriptors(self) -> list[dict[str, Any]]:
        """Filesystem metadata only — does not load weights."""
        descriptors: list[dict[str, Any]] = []
        for entry in self.discover_entries():
            artifact_dir = Path(entry["artifact_dir"])
            family = str(entry["family"])
            config_path = artifact_dir / "model_config.json"
            label_names: list[str] = []
            model_type = family
            if config_path.is_file():
                config = json.loads(config_path.read_text())
                label_names = list(config.get("label_names", []))
                model_type = str(config.get("model_type", family))
            load_error: str | None = None
            try:
                _load_backend(family, artifact_dir)
            except Exception as exc:  # noqa: BLE001
                load_error = str(exc)
            descriptors.append(
                {
                    **entry,
                    "model_type": model_type,
                    "label_names": label_names,
                    "artifact_dir": str(artifact_dir),
                    "load_error": load_error,
                }
            )
        return descriptors
