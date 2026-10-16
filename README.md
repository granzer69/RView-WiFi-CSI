# WiFi CSI Human Activity Recognition

Software-first pipeline for recognizing human activity from Wi-Fi channel state information. **V1** covers the data foundation (canonical CSI window, ESP-Fi adapter, session-grouped splits, preprocessing, simulator UI). **V2** adds leakage-checked training for classical and deep HAR models on ESP-Fi. **V3** exposes a FastAPI platform (HTTP + **WebSocket replay**), model picker, evaluation dashboard, and wires the simulator to live predictions — **without hardware**.

**Final scope:** software + ESP-Fi + replay + ML + dashboard only. See **`docs/project-scope.md`** (V4 ESP32 / V5 are not planned unless reopened).

| Doc | Purpose |
| --- | --- |
| **[`docs/SETUP.md`](docs/SETUP.md)** | **Start here** — clone, install, ESP-Fi, run API + UI, Cursor ports, env vars, troubleshooting |
| [`docs/what-we-built.md`](docs/what-we-built.md) | Architecture, V1–V3, measured results, limitations |
| [`docs/cursor-in-app-browser.md`](docs/cursor-in-app-browser.md) | Cursor Cloud port forwarding |

## Quick start

```bash
git clone https://github.com/granzer69/RView-WiFi-CSI.git && cd RView-WiFi-CSI
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ml]"
cd frontend && npm ci && cd ..
# Optional: place ESP-Fi under data/raw/esp-fi-har/ (see docs/SETUP.md)
bash scripts/dev-stack.sh start-preview
bash scripts/dev-stack.sh status
```

Open **http://127.0.0.1:43123** (forward **43123** and **45231** in Cursor Cloud). Full details: **`docs/SETUP.md`**.

## Data

ESP-Fi HAR is the primary dataset. Place the extracted archive at `data/raw/esp-fi-har/` (four environment directories, each with `mat/` and `csv/`). The archive is CC BY 4.0. Raw data is gitignored.

Activity codes follow the class folders in the published scenario-3 tree, not the README id table. Those two maps disagree for every code except `1` (run). Scenarios 1, 2, and 4 have no class folders, so their labels are inferred and marked unverified.

CSI-Bench is the secondary validation set. It is not downloaded here. Its data license is CC BY-NC-ND 4.0, and its code is reference-only.

Embedded WiFi Sensing HAR is optional and local for inspection only. Academic volunteer consent is not treated as a commercial-use grant. Experiment entry points raise until that status changes.

See `data/README.md` for paths, hashes, and the license flags.

## Run

Python 3.11 or newer. From the repository root:

```bash
python3 -m pip install -e ".[dev,ml]"
python3 scripts/inspect_esp_fi.py --plots artifacts/figures
python3 scripts/inspect_held_datasets.py
python3 -m pytest
```

`inspect_esp_fi.py` prints trial counts and writes:

- `reports/esp_fi_inspection.json`
- `reports/esp_fi_split_methodology.md`
- `data/metadata/esp-fi-har.json`

Splits use seed 42 and `floor(n * 0.15)` holdouts. The three strategies (`in_domain`, `cross_user`, `cross_environment`) are separate results. The published `train_amp` / `test_amp` folders are only a leakage check.

The default preprocess config keeps each trial unchanged. Clipping, z-scoring, and shorter windows are opt-in in `configs/preprocessing/default.json` and `src/preprocessing/pipeline.py`.

## Layout

| Path | Role |
| --- | --- |
| `src/ingestion/` | `CsiWindow` |
| `src/datasets/` | ESP-Fi adapter, grouped splits, leakage check, closed gates for the other two datasets |
| `src/preprocessing/` | Validation, optional MAD clip, optional z-score, in-session segments |
| `src/csi/` | Amplitude plot and subcarrier heatmap |
| `src/simulator/` | Dataset replay simulator (clock, session controller, `DatasetReplaySource`) |
| `src/api/` | V3 FastAPI platform (`/health`, `/models`, `/predict`, `WS /ws/stream`) |
| `frontend/` | Visual CSI Activity Simulator UI (Vite + React) |
| `configs/` | Dataset, preprocess, split, and experiment settings |
| `src/models/`, `src/training/` | V2 model ladder and experiment runners |
| `artifacts/` | Versioned training outputs (`v2_logreg`, `v2_rf`, `v2_mlp`, `v2_gbdt`, `v2_cnn1d`, `v2_gru`, `v2_tcn`) |
| `reports/` | Measured inspection and V2 experiment summaries |

## V2 ML/HAR engine

Canonical build doc: **`docs/v2-engine-build-guide.md`** (splits, contracts, integrity checklist, commands).

Train baselines on ESP-Fi (requires `data/raw/esp-fi-har/`):

```bash
python3 scripts/train_logreg.py
python3 scripts/train_rf.py
python3 scripts/train_cnn1d.py   # PyTorch via .[ml]
python3 scripts/train_gru.py
python3 scripts/export_evaluation_summary.py
```

Measured reports: `reports/v2_logreg_results.md`, `reports/v2_rf_results.md`, `reports/v2_cnn1d_results.md`, `reports/v2_gru_results.md`.

## Visual CSI Activity Simulator + V3 platform

Software replay dashboard for ESP-Fi trials. **Real** CSI amplitude comes from API WebSocket replay (when ESP-Fi is on the API host) or exported trial JSON. **Simulated position** stays labeled in the UI; model predictions use the V3 API (WebSocket-first, `POST /predict` fallback).

### Frontend dev server

**Cursor Cloud (integrated browser):** see **`docs/cursor-in-app-browser.md`**. From repo root:

```bash
bash scripts/dev-stack.sh start   # API :45231 + Vite :43123, no auto-open browser
bash scripts/dev-stack.sh status
```

Forward ports **43123** and **45231** in Cursor, then use the **globe** on **43123** to open the internal browser.

```bash
# Refresh manifest + demo trials (or --all-trials for every session)
PYTHONPATH=src python3 scripts/export_replay_manifest.py --export-trials 1-1-2-1 1-1-1-1
python3 scripts/export_evaluation_summary.py

cd frontend
npm install
BROWSER=none npm run dev
```

Vite listens on **`0.0.0.0:43123`** (`strictPort`, `open: false`). In Cursor, use the **forwarded** `http://127.0.0.1:43123` on your machine.

| Layer | Status |
| --- | --- |
| CSI heatmap / timeline | **Real** rows from WS replay or `frontend/public/replay/trials/*.json` |
| Session catalog | **Real** metadata (`manifest.json` or `GET /replay/manifest`) |
| Transport | **WebSocket `/ws/stream`** preferred; local JSON + HTTP fallback |
| Model picker | All V2 families / split strategies via `GET/PUT /models` |
| Evaluation | `/evaluation` page from `frontend/public/evaluation/summary.json` |
| Spatial panel | **Simulated** (`spatial.simulated: true`) |

Design: `docs/csi-activity-simulator-design.md`. Platform: `docs/v3-platform-build-guide.md`.

## V3 API

```bash
python3 scripts/run_api.py          # http://127.0.0.1:45231
cd frontend && npm run dev            # proxies /api and /ws → API
```

See **`docs/v3-platform-build-guide.md`** for endpoints, WebSocket replay, demo script, and integrity labels.

### Frontend production build check

```bash
cd frontend && npm run build
```
