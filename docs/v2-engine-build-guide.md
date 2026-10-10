# V2 ML/HAR engine — build guide

Canonical reference for how WiFi CSI HAR **V2** is implemented in this repository: data contracts, splits, preprocessing, model ladder, artifacts, and evaluation. Scope follows `.cursor/03_VERSION_ROADMAP.md` **V2 — ML/HAR Engine**.

## V2 goals and acceptance criteria

From the version roadmap, V2 must deliver:

| Theme | Requirement |
| --- | --- |
| Feature pipeline | Configurable extraction from `HarSample` amplitudes |
| Classical baselines | Comparable sklearn models on shared splits |
| Deep learning | At least one CNN-family and one sequence model |
| Evaluation | Accuracy, macro/weighted F1, precision, recall, confusion matrix, per-class metrics |
| Generalization | `in_domain`, `cross_user`, `cross_environment` where metadata allows |
| Registry | Reproducible bundles: model, preprocessing/normalization, label map, config, metrics |
| **V2 acceptance** | ≥3 model families, leakage-free evaluation, reproducible training, saved artifacts, auto-generated reports |

**Current ladder status**

| Model | Status | Report |
| --- | --- | --- |
| Logistic regression + classical features | **Done** | `reports/v2_logreg_results.md` |
| Random Forest + classical features | **Done** (this branch) | `reports/v2_rf_results.md` |
| 1D CNN + raw amplitude | **Done** (this branch) | `reports/v2_cnn1d_results.md` |
| GRU + raw amplitude | **Done** (this branch) | `reports/v2_gru_results.md` |

## Locked constraints (do not bypass without approval)

- **Dataset:** ESP-Fi HAR only for V2 experiments (`data/raw/esp-fi-har/`).
- **Splits:** Session-grouped strategies with **locked SHA-256** assignment hashes (see below). Published `train_amp` / `test_amp` folders are leakage-check only.
- **Contract:** Models consume `HarSample` (`src/ingestion/ml_contract.py`), not raw folder paths.
- **Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 have **no class folders** — labels are **INFERRED — NOT INDEPENDENTLY VERIFIED**. Do not silently “fix” labels.
- **Out of scope without approval:** FastAPI, WebSockets, ESP32 firmware, CSI-Bench download/training, Embedded dataset experiments, simulator live prediction wiring.

## End-to-end data flow

```text
ESP-Fi trial (.mat)
    → datasets.esp_fi.load_window → CsiWindow
    → preprocessing.pipeline.process (config from YAML)
    → har_sample_from_window → HarSample
         amplitude (950, 52), label_id, session/user/environment metadata
    → [classical path] ClassicalFeatureExtractor.fit(train) → transform
    → [deep path]    AmplitudeNormalizer.fit(train) → transform
    → model.train / predict
    → evaluation.metrics.classification_report_dict
    → artifacts/<experiment>/<run_id>/<strategy>/
    → reports/v2_*_results.md (measured numbers)
```

**HarSample** fields used in training: `amplitude`, `label_id`, `split`, `split_strategy`, `session_id`, `user_id`, `environment_id`. `metadata.source_path` is always `None` at the contract boundary.

## Split strategies and leakage rules

Implemented in `src/datasets/splits.py`, loaded via `src/training/esp_fi.py`.

| Strategy | Holdout axis | Train / val / test |
| --- | --- | --- |
| `in_domain` | Random session groups (seed 42, 15% val, 15% test) | Mixed users & environments |
| `cross_user` | Held-out **users** | Generalization to new participants |
| `cross_environment` | Held-out **scenarios/environments** | Generalization to new rooms/layouts |

**Leakage rules**

1. Split assignment is at **session** granularity (one trial = one session id `user-scenario-activity-trial`).
2. All samples from a session stay in one split.
3. Learned preprocessing (feature scaler, amplitude normalizer) is **fit on train only**, then applied to val/test.
4. Optional windowing (`window_length` / `hop`) never crosses sessions (input is one trial per session).
5. Locked hashes in `EXPECTED_ASSIGNMENT_SHA256` (`esp_fi.py`) must match when `verify_assignment_hash: true`.

| Strategy | Locked assignment SHA-256 |
| --- | --- |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` |

## Preprocessing (V1 pipeline, V2 default)

Config type: `PreprocessConfig` in `src/preprocessing/pipeline.py`.

Default experiment YAML (`clip_mad: false`, `normalize: none`, full trial) keeps each ESP-Fi trial as a single `(950, 52)` amplitude matrix.

| Step | Train-only? | Notes |
| --- | --- | --- |
| Validate finiteness / shape | — | Always |
| MAD clip | Per-window at load | Off by default |
| `per_window_zscore` | Per-window at load | Off by default |
| Temporal segments | — | Off unless `window_length` set |

**Learned steps (train-only fit)**

| Model family | Learner | Module |
| --- | --- | --- |
| LogReg, Random Forest | Standardize classical feature vectors | `features.classical.ClassicalFeatureExtractor` |
| CNN, GRU | Per-subcarrier mean/std over train batch | `features.amplitude_normalize.AmplitudeNormalizer` |

## Model ladder — implementations

### Logistic regression (`src/models/logreg.py`)

- **Input:** `(N, 950, 52)` amplitudes → classical features **635-D** (`classical_feature_dim(52)`).
- **Classifier:** `sklearn.linear_model.LogisticRegression`.
- **Config:** `configs/experiments/v2_logreg_esp_fi.yaml`
- **Script:** `scripts/train_logreg.py`
- **Artifacts:** `artifacts/v2_logreg/<run_id>/`

### Random Forest (`src/models/rf.py`)

- **Input:** Same classical features as logreg (shared extractor contract).
- **Classifier:** `sklearn.ensemble.RandomForestClassifier`.
- **Config:** `configs/experiments/v2_rf_esp_fi.yaml`
- **Script:** `scripts/train_rf.py`
- **Artifacts:** `artifacts/v2_rf/<run_id>/`

### 1D CNN (`src/models/cnn1d.py`)

- **Tensor contract** (`MODEL_INPUT_SHAPES["cnn_1d"]`): storage `(time, subcarriers)` → model `(batch, 52, 950)` channels-first.
- **Normalization:** `AmplitudeNormalizer` on train only.
- **Architecture:** Small Conv1d stack + adaptive pool + linear head.
- **Config:** `configs/experiments/v2_cnn1d_esp_fi.yaml`
- **Script:** `scripts/train_cnn1d.py` (requires `pip install -e ".[ml]"`)
- **Artifacts:** `artifacts/v2_cnn1d/<run_id>/` (`model.pt`, `amplitude_normalizer.json`, `model_config.json`)

### GRU (`src/models/gru.py`)

- **Tensor contract** (`MODEL_INPUT_SHAPES["gru"]`): `(batch, 950, 52)` time-major.
- **Normalization:** Same train-only `AmplitudeNormalizer`.
- **Architecture:** Single-layer GRU + linear head.
- **Config:** `configs/experiments/v2_gru_esp_fi.yaml`
- **Script:** `scripts/train_gru.py`
- **Artifacts:** `artifacts/v2_gru/<run_id>/`

**Note on `MODEL_INPUT_SHAPES`:** Entries for logreg/RF list flattened raw size `(49400,)` for documentation of raw amplitude layout; the implemented classical path uses **635-D** engineered features, not raw flatten.

## Feature / tensor contracts (summary)

| Model | Amplitude layout | Model input | Fit on train only |
| --- | --- | --- | --- |
| LogReg | `(950, 52)` | 635 classical features | `ClassicalFeatureExtractor` |
| Random Forest | `(950, 52)` | 635 classical features | `ClassicalFeatureExtractor` |
| 1D CNN | `(950, 52)` | `(52, 950)` after norm | `AmplitudeNormalizer` |
| GRU | `(950, 52)` | `(950, 52)` after norm | `AmplitudeNormalizer` |

Seven classes: `NORMALIZED_LABELS` in `ml_contract.py` (`running` … `falling`).

## Evaluation metrics and generalization reporting

All models use `evaluation.metrics.classification_report_dict`:

- `accuracy`, `macro_f1`, `weighted_f1`
- `per_class` precision / recall / F1 / support
- `confusion_matrix`
- `inference_latency` (per-sample ms mean/median/p95)
- `model_size_bytes`; deep models also log `parameter_count`

Reports under `reports/v2_*_results.md` cite **test** split metrics per strategy. Compare train vs test via `metrics.json` in each strategy folder to diagnose overfitting and domain shift.

## Artifact / registry layout

```text
artifacts/
  v2_logreg/<run_id>/
    manifest.json                 # experiment metadata, git commit, all strategies
    in_domain/
      classifier.joblib
      feature_extractor.json
      model_config.json
      metrics.json
    cross_user/ ...
    cross_environment/ ...
  v2_rf/<run_id>/                 # same sklearn layout as logreg
  v2_cnn1d/<run_id>/
    <strategy>/
      model.pt
      amplitude_normalizer.json
      model_config.json
      metrics.json
  v2_gru/<run_id>/                # same torch layout as cnn1d
```

`manifest.json` includes: `experiment`, `run_id`, `created_at`, `git_commit`, `dataset`, `seed`, `preprocess`, `model`, nested `strategies` test metrics, `label_map`, `label_note`.

## Reproducibility

- **Configs:** YAML under `configs/experiments/v2_*_esp_fi.yaml`.
- **Seed:** `seed: 42` drives split assignment (via `assign_splits`) and model RNG (`random_state` / `torch.manual_seed`).
- **Hashes:** Assignment SHA-256 verified at load when `verify_assignment_hash: true`.
- **Manifests:** Record git commit at train time (`training.experiment._git_commit`).
- **Dependencies:** `pyproject.toml` — core sklearn stack; `ml` extra adds PyTorch.

## Simulator integration policy

The V1 CSI Activity Simulator (`frontend/`, `src/simulator/`) replays real ESP-Fi trials with **stub** predictions. **V2 does not wire trained models into the simulator.** Defer until V3 defines a stable inference API and replay transport (roadmap V3.1–V3.2).

## Research integrity checklist

Before publishing or comparing numbers:

- [ ] ESP-Fi path present; split hashes match locked values.
- [ ] Label map documented; inferred scenarios called out in report and manifest.
- [ ] No test/val data used to fit scalers, normalizers, or feature statistics.
- [ ] Metrics taken from saved `metrics.json` / reports — not hand-edited.
- [ ] `git_commit` in manifest matches the branch you intend to cite.
- [ ] No CSI-Bench / Embedded / hardware data mixed into ESP-Fi V2 runs without explicit approval.

## How to run training and evaluation

Install:

```bash
python3 -m pip install -e ".[dev,ml]"
```

Train (full ESP-Fi, all three strategies):

```bash
python3 scripts/train_logreg.py
python3 scripts/train_rf.py
python3 scripts/train_cnn1d.py
python3 scripts/train_gru.py
```

Optional overrides:

```bash
python3 scripts/train_rf.py --config configs/experiments/v2_rf_esp_fi.yaml --run-id my_run_id
python3 scripts/train_rf.py --artifacts-root artifacts/v2_rf
```

Tests:

```bash
python3 -m pytest
```

Inspect results:

- Per-run: `artifacts/<family>/<run_id>/manifest.json`
- Human summary: `reports/v2_*_results.md`

## Related documents

- Version roadmap: `.cursor/03_VERSION_ROADMAP.md`
- V1 data report (project store): signed-off ESP-Fi methodology
- Logreg proposal: `reports/v2_logreg_experiment_proposal.md`
