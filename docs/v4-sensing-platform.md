# V4 Sensing Platform

V4 unifies dataset replay inference, source transparency, and three new workbench routes without retraining models or claiming live ESP32 capture.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/source/status` | `dataset_replay` when ESP-Fi root exists; otherwise `live_unavailable` (ESP32 stub not implemented) |
| GET | `/activity/trials` | Trial list for Activity workbench (no bulk inference) |
| POST | `/activity/sample` | Ground truth vs prediction at a sample index (prefix amplitude) |
| GET | `/explorer/catalog/export` | Bounded JSON export (`max_trials` query, default 500) |

Existing V3 routes (`/predict`, `WS /ws/stream`, `/explorer/*`, `/experiments/*`, `/models`) are unchanged.

### WebSocket replay fields

`csi_frame` and `prediction` payloads may include:

- `source`: `dataset_replay`
- `sample_index`, `sample_count`: trial row index (0–949), not seconds

## UI routes

| Route | Role |
|-------|------|
| `/` | Live sensing — replay transport, heatmap + subcarrier trace vs sample index |
| `/activity` | Trial list, on-demand inference, misclass → `/explorer?session=` |
| `/models` | 7 families × 3 strategies from `evaluation/summary.json` + `research/generalization.json` |
| `/explorer` | CSI explorer (quality flags on catalog trials) |
| `/evaluation`, `/research`, `/experiments` | Unchanged |

Shell header shows persistent source badge from `GET /source/status`.

## Data

Symlink ESP-Fi at `data/raw/esp-fi-har` (not committed). Amplitude contract remains `(950, 52)`.

## Constraints

- Frozen `artifacts/v2_*` only; missing metrics display as **unavailable**, never `0`.
- Spatial panel stays simulated; no localization or presence-classifier claims.
