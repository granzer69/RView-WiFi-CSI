# CSI Explorer + Experiment Workbench — Design

**Branch:** `feature/csi-explorer-experiment-workbench`  
**Baseline `main`:** `ebbfd301e3da06147e47d41982bb4b98aa322f19`  
**Audit dependency:** Cherry-picked `d6a7324` (`docs/research-validity-audit.md`) onto the feature branch.

## Goals

1. **CSI Explorer (`/explorer`)** — inspect real ESP-Fi amplitude trials (950×52), compare recordings, and align trial-level model predictions with ground-truth labels (verified vs inferred).
2. **Experiment Workbench (`/experiments`)** — configure and launch training through the existing v2 pipeline into `artifacts/workbench/`, with a filesystem registry and metrics dashboard.

## Locked constraints (preserved)

- ESP-Fi primary dataset; session-grouped splits unchanged.
- Four model families (logreg, rf, cnn1d, gru); no ESP32/V5/DB rewrite.
- Amplitude shape (950, 52); API ports 43123 (Vite) / 45231 (FastAPI).
- No raw ESP-Fi archive in git; no invented metrics or sampling rates.
- Frozen baseline artifacts under `artifacts/v2_*` baseline run IDs are read-only for this workbench.
- Replay WebSocket and existing research API remain compatible; new routes are additive.

## Code map (inspected)

| Area | Location | Role |
| --- | --- | --- |
| Dataset adapter | `src/datasets/esp_fi.py` | Trial discovery, `load_window()`, label verification flags |
| Replay manifest | `src/api/replay_manifest.py` | Session list for Sensing Studio |
| Inference | `src/api/inference.py` | Trial/window `predict_from_amplitude` |
| Training | `src/training/experiment.py`, `deep_experiment.py` | logreg/rf and cnn1d/gru experiment runners |
| Features | `src/features/classical.py` | `ClassicalFeatureExtractor` (fixed group layout) |
| Visualization reference | `src/csi/visualize.py` | Heatmap orientation: `imshow(amplitude.T)`, origin lower |
| Frontend shell | `frontend/src/components/layout/WorkspaceShell.tsx` | Sensing Studio nav |

## Phase 1 — CSI Explorer

### API (`src/api/explorer_service.py`, wired in `src/api/main.py`)

| Endpoint | Purpose |
| --- | --- |
| `GET /explorer/catalog` | Trial metadata from `discover_trials` |
| `GET /explorer/trials/{session_id}` | Detail + `signal_statistics()` |
| `GET /explorer/trials/{session_id}/amplitude` | Bounded raw amplitude slice (max 950 rows) |
| `GET /explorer/trials/{session_id}/subcarrier/{i}` | Raw amplitude time series for one subcarrier |
| `GET /explorer/compare` | Side-by-side metadata + shared min/max scale |
| `GET /explorer/trials/{session_id}/prediction` | Full-trial model prediction + GT label |

**Orientation:** matrices are `(time_steps, subcarriers)`. Heatmaps use sample index on X and subcarrier on Y (consistent with `save_heatmap`).

**Missing data:** catalog returns 404 when `RVIEW_DATA_ROOT` is absent; UI shows explicit empty state.

### UI (`frontend/src/pages/ExplorerPage.tsx`)

Recording filters (participant, scenario, activity), verified/inferred badges, compare mode with shared color scale, subcarrier inspector (raw amplitude), statistics panel, trial-level prediction card.

## Phase 2 — Experiment Workbench

### API (`src/api/workbench.py`)

| Endpoint | Purpose |
| --- | --- |
| `GET /experiments/schema` | Supported families, strategies, hyperparameter schema |
| `POST /experiments/runs` | `preview_only` or async start (thread worker, concurrency 1) |
| `GET /experiments/runs` | Registry from `artifacts/workbench/registry.json` |
| `GET /experiments/runs/{id}/metrics` | Read `metrics.json` per strategy |
| `POST /experiments/compare` | Compare test macro-F1 with split hash compatibility check |

Outputs: `artifacts/workbench/<family>/<run_id>/` plus `workbench_config.yaml` for CLI reproduction.

### UI (`frontend/src/pages/ExperimentsPage.tsx`)

Family/seed/strategy toggles, hyperparameter fields from schema, preview JSON, run list with polling, metrics viewer.

## Phase 3 — Feature ablation

**Deferred.** `ClassicalFeatureExtractor` builds a single concatenated vector (`PER_SUBCARRIER_STATS`, `GLOBAL_STATS`, `SPECTRAL_STATS`) with no runtime group toggles. Adding ablation would require extending `classical_feature_vector()` and retraining paths — out of scope for this slice.

## Phase 4–6 — Design system, schemas, tests, docs

- Reuses Sensing Studio cards, badges, zinc/cyan palette.
- Pydantic: `ExplorerCatalogResponse`, `AmplitudeSliceResponse`, `ExperimentRunRequest` in `src/api/schemas.py`.
- Tests: `tests/test_explorer_workbench_api.py` (synthetic MAT fixture).
- User guides: `docs/csi-explorer-user-guide.md`, `docs/experiment-workbench-guide.md`.

## Research safeguards

Follow `docs/research-validity-audit.md`: surface inferred labels, trial-level (not streaming) predictions, workbench writes only under `artifacts/workbench/`.
