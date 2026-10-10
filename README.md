# WiFi CSI Human Activity Recognition

Software-first pipeline for recognizing human activity from Wi-Fi channel state information. **V1** covers the data foundation (canonical CSI window, ESP-Fi adapter, session-grouped splits, preprocessing, simulator UI). **V2** adds leakage-checked training for classical and deep HAR models on ESP-Fi. **V3** exposes a FastAPI platform (HTTP inference + dataset replay WebSocket) and wires the simulator to real RF predictions.

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
| `frontend/` | Visual CSI Activity Simulator UI (Vite + React) |
| `configs/` | Dataset, preprocess, split, and experiment settings |
| `src/models/`, `src/training/` | V2 model ladder and experiment runners |
| `artifacts/` | Versioned training outputs (`v2_logreg`, `v2_rf`, `v2_cnn1d`, `v2_gru`) |
| `reports/` | Measured inspection and V2 experiment summaries |

## V2 ML/HAR engine

Canonical build doc: **`docs/v2-engine-build-guide.md`** (splits, contracts, integrity checklist, commands).

Train baselines on ESP-Fi (requires `data/raw/esp-fi-har/`):

```bash
python3 scripts/train_logreg.py
python3 scripts/train_rf.py
python3 scripts/train_cnn1d.py   # PyTorch via .[ml]
python3 scripts/train_gru.py
```

Measured reports: `reports/v2_logreg_results.md`, `reports/v2_rf_results.md`, `reports/v2_cnn1d_results.md`, `reports/v2_gru_results.md`.

## Visual CSI Activity Simulator (V1 slice)

Software replay dashboard for ESP-Fi trials. **Real** CSI amplitude comes from exported `.mat` trials (or live Python `load_window()` in tests). **Simulated position** and **stub model predictions** are clearly labeled in the UI — no trained model yet.

### Frontend dev server

```bash
# Optional: refresh manifest + demo trial JSON from local ESP-Fi archive
PYTHONPATH=src python3 scripts/export_replay_manifest.py --export-trials 1-1-2-1 1-1-1-1

cd frontend
npm install
npm run dev
```

Dev server: **http://127.0.0.1:43123** (`vite.config.ts`).

| Layer | V1 status |
| --- | --- |
| CSI heatmap / timeline | **Real** rows from `frontend/public/replay/trials/*.json` (exported MAT) |
| Session catalog | **Real** metadata in `manifest.json` (all 2240 sessions) |
| Transport | In-browser `LocalReplayTransport` (not FastAPI/WebSocket) |
| Model prediction card | **Stub** (`stub_v1_no_training`) for UI wiring only |
| Spatial panel | **Simulated** (`spatial.simulated: true`) |

Design: `docs/csi-activity-simulator-design.md`.

### Frontend production build check

```bash
cd frontend && npm run build
```
