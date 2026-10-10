# V2 baseline experiment proposal — logistic regression (classical features)

## Scope (this run only)

- Dataset: **ESP-Fi HAR** (`esp-fi-har`), software-first path only.
- Model: **multinomial logistic regression** on hand-crafted amplitude statistics.
- Out of scope until user approval: Random Forest, CNN, GRU, simulator prediction wiring, new split definitions.

## Labels and integrity

- Label map: `published_folder_codes_not_readme` (locked).
- Scenarios 1, 2, and 4: labels are **INFERRED — NOT INDEPENDENTLY VERIFIED** (no class folders); documented in artifacts, no silent relabeling.
- Splits: existing session-grouped strategies with **locked assignment SHA-256** verification (`assign_splits`, seed 42, 15% val/test).

| Strategy | Train | Val | Test | Assignment SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `in_domain` | 1792 | 224 | 224 | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` |
| `cross_user` | 1680 | 280 | 280 | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` |
| `cross_environment` | 1120 | 560 | 560 | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` |

## Input contract

- Consume `HarSample` via `har_sample_from_window` after V1 preprocessing (`PreprocessConfig` default: validate only, one full trial segment).
- Amplitude layout: `(950, 52)` time × subcarriers.

## Features (`classical_v1`)

Per subcarrier (52 × 10): mean, std, var, min, max, range, RMS, energy, skew, kurtosis.

Global (11): same stats over all samples plus histogram entropy.

Spectral per subcarrier (52 × 2): mean and std of `|rfft|` along time.

**Dimension:** 635 features per trial.

Learned preprocessing: `ClassicalFeatureExtractor` fits **per-feature mean/std on train only**, applied to val/test (no session or recording leakage).

## Model

- `sklearn.linear_model.LogisticRegression`, `solver=lbfgs`, `C=1.0`, `max_iter=2000`, `random_state=42`.
- Train on **train** split; report **val** and **test** metrics (val for sanity check, test for headline numbers).

## Metrics

For each strategy and split (val, test):

- Accuracy, macro-F1, weighted-F1
- Per-class precision / recall / F1 / support
- Confusion matrix (7 classes, normalized label order)
- Inference latency (per-sample ms, mean/median/p95 on test features)
- Model size (serialized classifier + scaler JSON bytes)

## Reproducibility

- Config: `configs/experiments/v2_logreg_esp_fi.yaml`
- CLI: `python3 scripts/train_logreg.py --config configs/experiments/v2_logreg_esp_fi.yaml`
- Seed: 42
- Git commit recorded in manifest

## Artifact layout

```
artifacts/v2_logreg/<run_id>/
  manifest.json
  in_domain/
    classifier.joblib
    feature_extractor.json
    model_config.json
    metrics.json
  cross_user/
    ...
  cross_environment/
    ...
```

`manifest.json` aggregates all strategies, dataset metadata, preprocess config, and measured test metrics.

## Success criteria

- All three split strategies train and evaluate without hash mismatch.
- Full `pytest` suite passes (including new training/inference contract tests).
- `reports/v2_logreg_results.md` contains **measured** numbers from the artifact run (no placeholders).
