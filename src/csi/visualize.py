"""Amplitude traces and subcarrier heatmaps.

Plots are written to files. Matplotlib is forced onto the non-interactive
backend so a missing display does not change the image.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ingestion.schema import CsiWindow


def save_amplitude_plot(window: CsiWindow, path: Path) -> None:
    """Plot the mean across subcarriers and three individual subcarriers."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    time_axis = np.arange(window.n_times)
    mean_trace = window.amplitude.mean(axis=1)
    picks = _subcarrier_picks(window.subcarriers)
    figure, axis = plt.subplots(figsize=(8, 3.5))
    axis.plot(time_axis, mean_trace, color="#1f4e79", linewidth=1.2, label="mean")
    for subcarrier in picks:
        axis.plot(
            time_axis,
            window.amplitude[:, subcarrier],
            linewidth=0.8,
            alpha=0.85,
            label=f"subcarrier {subcarrier}",
        )
    axis.set_xlabel("Time index")
    axis.set_ylabel("Amplitude")
    axis.set_title(_title(window, "amplitude"))
    axis.legend(loc="upper right", fontsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    plt.close(figure)


def save_heatmap(window: CsiWindow, path: Path) -> None:
    """Plot subcarriers against time. No interpolation is applied."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 3.5))
    image = axis.imshow(
        window.amplitude.T,
        aspect="auto",
        origin="lower",
        interpolation="nearest",
        cmap="viridis",
    )
    axis.set_xlabel("Time index")
    axis.set_ylabel("Subcarrier")
    axis.set_title(_title(window, "heatmap"))
    figure.colorbar(image, ax=axis, label="Amplitude")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    plt.close(figure)


def _subcarrier_picks(n_subcarriers: int) -> list[int]:
    if n_subcarriers < 3:
        return list(range(n_subcarriers))
    return [0, n_subcarriers // 2, n_subcarriers - 1]


def _title(window: CsiWindow, kind: str) -> str:
    label = window.metadata.get("normalized_label", "csi")
    session = window.session_id or "session"
    return f"{label} / {session} / {kind}"
