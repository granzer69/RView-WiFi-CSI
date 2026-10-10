"""GRU sequence model on amplitude (time, subcarriers)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from common.errors import DatasetError
from evaluation.metrics import classification_report_dict, measure_inference_latency_ms
from features.amplitude_normalize import AmplitudeNormalizer
from ingestion.ml_contract import NORMALIZED_LABELS

try:
    import torch
    import torch.nn as nn
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]


def _require_torch() -> Any:
    if torch is None:
        raise DatasetError("PyTorch is required; install with pip install -e '.[ml]'")
    return torch


class GruBackbone(nn.Module if nn else object):  # type: ignore[misc]
    def __init__(self, n_subcarriers: int, n_classes: int, hidden_size: int = 64) -> None:
        _require_torch()
        super().__init__()
        self.gru = nn.GRU(
            input_size=n_subcarriers,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
        )
        self.head = nn.Linear(hidden_size, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(x)
        last = out[:, -1, :]
        return self.head(last)


@dataclass
class GruHarModel:
    network: Any
    normalizer: AmplitudeNormalizer
    label_names: tuple[str, ...]
    config: dict[str, Any]
    device: str

    def _to_tensor_batch(self, amplitudes: np.ndarray) -> torch.Tensor:
        torch_mod = _require_torch()
        normed = self.normalizer.transform(amplitudes)
        if normed.ndim == 2:
            normed = normed[None, ...]
        return torch_mod.as_tensor(normed, dtype=torch_mod.float32, device=self.device)

    def predict(self, amplitudes: np.ndarray) -> np.ndarray:
        torch_mod = _require_torch()
        self.network.eval()
        with torch_mod.no_grad():
            logits = self.network(self._to_tensor_batch(amplitudes))
            return logits.argmax(dim=1).cpu().numpy()

    def evaluate(self, amplitudes: np.ndarray, label_ids: np.ndarray) -> dict[str, Any]:
        predictions = self.predict(amplitudes)
        metrics = classification_report_dict(label_ids, predictions, labels=self.label_names)
        probe = amplitudes[: min(8, amplitudes.shape[0])]
        latency = measure_inference_latency_ms(
            lambda _batch: self.predict(probe),
            np.zeros((probe.shape[0], 1), dtype=np.float64),
        )
        metrics["inference_latency"] = latency
        metrics["model_size_bytes"] = self.artifact_size_bytes()
        metrics["parameter_count"] = sum(p.numel() for p in self.network.parameters())
        return metrics

    def artifact_size_bytes(self) -> int:
        torch_mod = _require_torch()
        import io

        buffer = io.BytesIO()
        torch_mod.save(self.network.state_dict(), buffer)
        return buffer.tell() + len(json.dumps(self.normalizer.to_dict()).encode("utf-8"))

    def save(self, directory: Path) -> None:
        torch_mod = _require_torch()
        directory.mkdir(parents=True, exist_ok=True)
        torch_mod.save(self.network.state_dict(), directory / "model.pt")
        (directory / "amplitude_normalizer.json").write_text(
            json.dumps(self.normalizer.to_dict(), indent=2) + "\n"
        )
        (directory / "model_config.json").write_text(json.dumps(self.config, indent=2) + "\n")

    @classmethod
    def load(cls, directory: Path, device: str = "cpu") -> GruHarModel:
        torch_mod = _require_torch()
        config = json.loads((directory / "model_config.json").read_text())
        normalizer = AmplitudeNormalizer.from_dict(
            json.loads((directory / "amplitude_normalizer.json").read_text())
        )
        n_sub = int(config["n_subcarriers"])
        hidden = int(config.get("hidden_size", 64))
        n_classes = len(config.get("label_names", NORMALIZED_LABELS))
        network = GruBackbone(n_sub, n_classes, hidden_size=hidden)
        network.load_state_dict(torch_mod.load(directory / "model.pt", map_location=device))
        network.to(device)
        return cls(
            network=network,
            normalizer=normalizer,
            label_names=tuple(config.get("label_names", NORMALIZED_LABELS)),
            config=config,
            device=device,
        )


def train_gru(
    train_amplitudes: np.ndarray,
    train_labels: np.ndarray,
    val_amplitudes: np.ndarray,
    val_labels: np.ndarray,
    *,
    random_state: int = 42,
    epochs: int = 8,
    batch_size: int = 32,
    learning_rate: float = 1e-3,
    hidden_size: int = 64,
    device: str = "cpu",
    extra_config: dict[str, Any] | None = None,
) -> GruHarModel:
    from training.torch_loop import train_supervised_epochs

    _require_torch()
    if train_amplitudes.ndim != 3:
        raise DatasetError(f"train_amplitudes must be 3D, got {train_amplitudes.shape}")
    np.random.seed(random_state)

    n_sub = int(train_amplitudes.shape[2])
    normalizer = AmplitudeNormalizer().fit(train_amplitudes)
    network = GruBackbone(n_sub, len(NORMALIZED_LABELS), hidden_size=hidden_size).to(device)

    train_supervised_epochs(
        network,
        normalizer,
        train_amplitudes,
        train_labels,
        val_amplitudes,
        val_labels,
        layout="gru",
        device=device,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        random_state=random_state,
    )

    config = {
        "model_type": "gru",
        "input_layout": "time_major_subcarriers",
        "n_subcarriers": n_sub,
        "n_times": int(train_amplitudes.shape[1]),
        "hidden_size": hidden_size,
        "random_state": random_state,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "label_names": list(NORMALIZED_LABELS),
        **(extra_config or {}),
    }
    return GruHarModel(
        network=network,
        normalizer=normalizer,
        label_names=NORMALIZED_LABELS,
        config=config,
        device=device,
    )
