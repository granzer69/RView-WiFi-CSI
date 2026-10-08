# WiFi CSI Human Activity Recognition

Software-first pipeline for recognizing human activity from Wi-Fi channel state information. This repository currently covers the data foundation: a canonical CSI window, the ESP-Fi HAR adapter, session-grouped splits, preprocessing switches, and inspection plots. It does not train a model, serve an API, or talk to hardware.

## Data

ESP-Fi HAR is the primary dataset. Place the extracted archive at `data/raw/esp-fi-har/` (four environment directories, each with `mat/` and `csv/`). The archive is CC BY 4.0. Raw data is gitignored.

Activity codes follow the class folders in the published scenario-3 tree, not the README id table. Those two maps disagree for every code except `1` (run). Scenarios 1, 2, and 4 have no class folders, so their labels are inferred and marked unverified.

CSI-Bench is the secondary validation set. It is not downloaded here. Its data license is CC BY-NC-ND 4.0, and its code is reference-only.

Embedded WiFi Sensing HAR is optional and local for inspection only. Academic volunteer consent is not treated as a commercial-use grant. Experiment entry points raise until that status changes.

See `data/README.md` for paths, hashes, and the license flags.

## Run

Python 3.11 or newer. From the repository root:

```bash
python -m pip install -e ".[dev]"
python scripts/inspect_esp_fi.py --plots artifacts/figures
python scripts/inspect_held_datasets.py
python -m pytest
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
| `configs/` | Dataset, preprocess, and split settings |
| `reports/` | Measured inspection output |
