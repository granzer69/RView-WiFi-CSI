"""Simulated floor-plan coordinates (matches frontend replayClient.spatialAt)."""

from __future__ import annotations

import math


def simulated_spatial(progress: float, label: str) -> dict[str, float | bool]:
    t = progress
    x = 0.5
    y = 0.5
    if label in ("walking", "running"):
        x = 0.2 + 0.6 * abs(math.sin(t * math.pi * 2))
        y = 0.5
    elif label == "falling":
        x = 0.5
        y = 0.5 - 0.35 * min(1.0, t * 4)
    elif label == "jumping":
        y = 0.5 - 0.25 * abs(math.sin(t * math.pi * 4))
        x = 0.5
    else:
        x = 0.5 + 0.15 * math.sin(t * math.pi)
        y = 0.5 + 0.1 * math.cos(t * math.pi)
    return {"x": x, "y": y, "simulated": True}
