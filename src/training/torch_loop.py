"""Shared PyTorch mini-batch training for V2 deep models."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np

from features.amplitude_normalize import AmplitudeNormalizer
from ingestion.ml_contract import NORMALIZED_LABELS


def _to_tensor_batch(
    amplitudes: np.ndarray,
    normalizer: AmplitudeNormalizer,
    layout: Literal["cnn", "gru"],
    device: str,
) -> Any:
    import torch

    normed = normalizer.transform(amplitudes)
    if normed.ndim == 2:
        normed = normed[None, ...]
    if layout == "cnn":
        channels_first = np.transpose(normed, (0, 2, 1))
        return torch.as_tensor(channels_first, dtype=torch.float32, device=device)
    return torch.as_tensor(normed, dtype=torch.float32, device=device)


def train_supervised_epochs(
    network: Any,
    normalizer: AmplitudeNormalizer,
    train_x: np.ndarray,
    train_y: np.ndarray,
    val_x: np.ndarray,
    val_y: np.ndarray,
    *,
    layout: Literal["cnn", "gru"],
    device: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    random_state: int,
) -> None:
    import torch

    torch.manual_seed(random_state)
    optimizer = torch.optim.Adam(network.parameters(), lr=learning_rate)
    criterion = torch.nn.CrossEntropyLoss()

    for epoch in range(epochs):
        network.train()
        indices = np.arange(train_x.shape[0])
        rng = np.random.default_rng(random_state + epoch)
        rng.shuffle(indices)
        for start in range(0, train_x.shape[0], batch_size):
            batch_idx = indices[start : start + batch_size]
            batch_x = train_x[batch_idx]
            batch_y = train_y[batch_idx]
            tensor_x = _to_tensor_batch(batch_x, normalizer, layout, device)
            tensor_y = torch.as_tensor(batch_y, dtype=torch.long, device=device)
            optimizer.zero_grad()
            logits = network(tensor_x)
            loss = criterion(logits, tensor_y)
            loss.backward()
            optimizer.step()

        network.eval()
        with torch.no_grad():
            val_logits = network(_to_tensor_batch(val_x, normalizer, layout, device))
            _ = criterion(val_logits, torch.as_tensor(val_y, dtype=torch.long, device=device))
