# CSI Explorer — User Guide

## Open the explorer

1. Start the stack (`./dev-stack.sh` or API on port **45231** and Vite on **43123**).
2. Navigate to **CSI Explorer** in the header (`/explorer`).

## Requirements

ESP-Fi MAT files must be present at `RVIEW_DATA_ROOT` (default `data/raw/esp-fi-har`). The repository does not ship raw data.

## Selecting recordings

Use filters for participant, scenario, and activity. Each trial shows:

- **verified** — label confirmed by published class folder (scenario 3).
- **inferred** — scenarios 1, 2, 4 (see label caveat banner).

Enable **Compare two recordings** to view side-by-side heatmaps with a shared amplitude color scale.

## Heatmap

- **Horizontal axis:** sample index (0…949), not seconds.
- **Vertical axis:** subcarrier index (0…51).
- **Values:** raw `CSIamp` amplitude from the MAT file (not preprocessed features).
- Use region start/end to zoom a sample range; hover cells for tooltips.

## Subcarrier inspector

Pick a subcarrier index to plot **raw amplitude vs sample index** for the selected trial.

## Predictions

When a model artifact is loaded, the page requests a **trial-level** prediction using the full 950×52 matrix. Ground truth is the trial’s normalized activity label. Confidence and per-class probabilities appear when the model exposes `predict_proba`.
