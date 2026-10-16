"""Lightweight temporal convolution network on raw amplitude.

Architecture: stacked dilated Conv1d blocks (channels=subcarriers, length=time)
with residual connections, then global average pooling and a linear head.
Same input layout as the 1D CNN baseline (channels-first subcarriers × time).
"""

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


class _TcnBlock(nn.Module if nn else object):  # type: ignore[misc]
    def __init__(self, channels: int, kernel_size: int, dilation: int) -> None:
        _require_torch()
        super().__init__()
        padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(channels, channels, kernel_size, padding=padding, dilation=dilation)
        self.relu = nn.ReLU(inplace=True)
        self.kernel_size = kernel_size
        self.dilation = dilation

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv(x)
        trim = (self.kernel_size - 1) * self.dilation
        if trim > 0:
            out = out[:, :, :-trim]
        return self.relu(out + x)


class TcnBackbone(nn.Module if nn else object):  # type: ignore[misc]
    """Three dilated residual blocks + adaptive pool."""

    def __init__(self, n_subcarriers: int, n_classes: int, channels: int = 64) -> None:
        _require_torch()
        super().__init__()
        self.stem = nn.Conv1d(n_subcarriers, channels, kernel_size=1)
        self.blocks = nn.Sequential(
            _TcnBlock(channels, kernel_size=3, dilation=1),
            _TcnBlock(channels, kernel_size=3, dilation=2),
            _TcnBlock(channels, kernel_size=3, dilation=4),
        )
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Linear(channels, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.blocks(x)
        x = self.pool(x).squeeze(-1)
        return self.head(x)


@dataclass
class TcnHarModel:
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
        channels_first = np.transpose(normed, (0, 2, 1))
        return torch_mod.as_tensor(channels_first, dtype=torch_mod.float32, device=self.device)

    def predict(self, amplitudes: np.ndarray) -> np.ndarray:
        return self.predict_proba(amplitudes).argmax(axis=1)

    def predict_proba(self, amplitudes: np.ndarray) -> np.ndarray:
        torch_mod = _require_torch()
        self.network.eval()
        with torch_mod.no_grad():
            logits = self.network(self._to_tensor_batch(amplitudes))
            return torch_mod.softmax(logits, dim=1).cpu().numpy()

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
    def load(cls, directory: Path, device: str = "cpu") -> TcnHarModel:
        torch_mod = _require_torch()
        config = json.loads((directory / "model_config.json").read_text())
        normalizer = AmplitudeNormalizer.from_dict(
            json.loads((directory / "amplitude_normalizer.json").read_text())
        )
        n_sub = int(config["n_subcarriers"])
        channels = int(config.get("channels", 64))
        n_classes = len(config.get("label_names", NORMALIZED_LABELS))
        network = TcnBackbone(n_sub, n_classes, channels=channels)
        network.load_state_dict(torch_mod.load(directory / "model.pt", map_location=device))
        network.to(device)
        return cls(
            network=network,
            normalizer=normalizer,
            label_names=tuple(config.get("label_names", NORMALIZED_LABELS)),
            config=config,
            device=device,
        )


def train_tcn(
    train_amplitudes: np.ndarray,
    train_labels: np.ndarray,
    val_amplitudes: np.ndarray,
    val_labels: np.ndarray,
    *,
    random_state: int = 42,
    epochs: int = 8,
    batch_size: int = 32,
    learning_rate: float = 1e-3,
    device: str = "cpu",
    channels: int = 64,
    extra_config: dict[str, Any] | None = None,
) -> TcnHarModel:
    from training.torch_loop import train_supervised_epochs

    torch_mod = _require_torch()
    if train_amplitudes.ndim != 3:
        raise DatasetError(f"train_amplitudes must be 3D, got {train_amplitudes.shape}")
    np.random.seed(random_state)

    n_sub = int(train_amplitudes.shape[2])
    n_classes = len(NORMALIZED_LABELS)
    normalizer = AmplitudeNormalizer().fit(train_amplitudes)
    network = TcnBackbone(n_sub, n_classes, channels=channels).to(device)

    train_supervised_epochs(
        network,
        normalizer,
        train_amplitudes,
        train_labels,
        val_amplitudes,
        val_labels,
        layout="cnn",
        device=device,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        random_state=random_state,
    )

    config = {
        "model_type": "tcn",
        "input_layout": "channels_first_subcarriers_time",
        "architecture_note": "dilated residual Conv1d blocks (d=1,2,4) + global avg pool",
        "n_subcarriers": n_sub,
        "n_times": int(train_amplitudes.shape[1]),
        "channels": channels,
        "random_state": random_state,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "label_names": list(NORMALIZED_LABELS),
        **(extra_config or {}),
    }
    return TcnHarModel(
        network=network,
        normalizer=normalizer,
        label_names=NORMALIZED_LABELS,
        config=config,
        device=device,
    )
