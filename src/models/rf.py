"""Random forest baseline with classical features."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from common.errors import DatasetError
from evaluation.metrics import classification_report_dict, measure_inference_latency_ms
from features.classical import ClassicalFeatureExtractor
from ingestion.ml_contract import NORMALIZED_LABELS


@dataclass
class RandomForestHarModel:
    """Fitted random forest plus train-only feature scaling."""

    classifier: RandomForestClassifier
    feature_extractor: ClassicalFeatureExtractor
    label_names: tuple[str, ...]
    config: dict[str, Any]

    def predict(self, amplitudes: np.ndarray) -> np.ndarray:
        features = self.feature_extractor.transform(amplitudes)
        return self.classifier.predict(features)

    def predict_proba(self, amplitudes: np.ndarray) -> np.ndarray:
        features = self.feature_extractor.transform(amplitudes)
        return self.classifier.predict_proba(features)

    def evaluate(self, amplitudes: np.ndarray, label_ids: np.ndarray) -> dict[str, Any]:
        predictions = self.predict(amplitudes)
        metrics = classification_report_dict(label_ids, predictions, labels=self.label_names)
        feature_matrix = self.feature_extractor.transform(amplitudes)
        latency = measure_inference_latency_ms(
            lambda batch: self.classifier.predict(batch),
            feature_matrix,
        )
        metrics["inference_latency"] = latency
        metrics["model_size_bytes"] = self.artifact_size_bytes()
        return metrics

    def artifact_size_bytes(self) -> int:
        buffer = io.BytesIO()
        joblib.dump(self.classifier, buffer)
        return buffer.tell() + len(json.dumps(self.feature_extractor.to_dict()).encode("utf-8"))

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.classifier, directory / "classifier.joblib")
        (directory / "feature_extractor.json").write_text(
            json.dumps(self.feature_extractor.to_dict(), indent=2) + "\n"
        )
        (directory / "model_config.json").write_text(json.dumps(self.config, indent=2) + "\n")

    @classmethod
    def load(cls, directory: Path) -> RandomForestHarModel:
        config = json.loads((directory / "model_config.json").read_text())
        extractor = ClassicalFeatureExtractor.from_dict(
            json.loads((directory / "feature_extractor.json").read_text())
        )
        classifier = joblib.load(directory / "classifier.joblib")
        return cls(
            classifier=classifier,
            feature_extractor=extractor,
            label_names=tuple(config.get("label_names", NORMALIZED_LABELS)),
            config=config,
        )


def train_random_forest(
    train_amplitudes: np.ndarray,
    train_labels: np.ndarray,
    *,
    random_state: int = 42,
    n_estimators: int = 200,
    max_depth: int | None = None,
    min_samples_leaf: int = 1,
    class_weight: str | dict[int, float] | None = None,
    n_jobs: int = -1,
    extra_config: dict[str, Any] | None = None,
) -> RandomForestHarModel:
    if train_amplitudes.ndim != 3:
        raise DatasetError(f"train_amplitudes must be 3D, got {train_amplitudes.shape}")
    extractor = ClassicalFeatureExtractor().fit(train_amplitudes)
    features = extractor.transform(train_amplitudes)
    classifier = RandomForestClassifier(
        random_state=random_state,
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        class_weight=class_weight,
        n_jobs=n_jobs,
    )
    classifier.fit(features, train_labels)
    config = {
        "model_type": "random_forest",
        "feature_kind": "classical_v1",
        "random_state": random_state,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "min_samples_leaf": min_samples_leaf,
        "class_weight": class_weight,
        "n_jobs": n_jobs,
        "label_names": list(NORMALIZED_LABELS),
        **(extra_config or {}),
    }
    return RandomForestHarModel(
        classifier=classifier,
        feature_extractor=extractor,
        label_names=NORMALIZED_LABELS,
        config=config,
    )
