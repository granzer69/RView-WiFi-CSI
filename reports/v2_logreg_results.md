# V2 logistic regression baseline — measured results

Run: `20261010T045500Z` (artifacts under `artifacts/v2_logreg/20261010T045500Z/`).  
Config: `configs/experiments/v2_logreg_esp_fi.yaml`.  
Proposal: `reports/v2_logreg_experiment_proposal.md`.

**Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 are **INFERRED — NOT INDEPENDENTLY VERIFIED** (see manifest `label_note`).

**Preprocessing:** V1 default (validate only, one full trial, no global z-score). Classical feature scaler fit on **train** only.

## Split verification

| Strategy | Assignment SHA-256 (locked) | Train | Val | Test |
| --- | --- | ---: | ---: | ---: |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` | 1792 | 224 | 224 |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` | 1680 | 280 | 280 |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` | 1120 | 560 | 560 |

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 | Model size (bytes) | Inference (ms/sample, mean) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `in_domain` | 0.5446 | 0.5385 | 0.5385 | 61125 | 0.00072 |
| `cross_user` | 0.4286 | 0.3974 | 0.3974 | 61153 | 0.00076 |
| `cross_environment` | 0.2696 | 0.2564 | 0.2564 | 61124 | 0.00066 |

Training wall time per strategy (includes full ESP-Fi load + feature extraction): in_domain 277s, cross_user 280s, cross_environment 243s.

## Test per-class F1 (`in_domain`)

| Class | F1 | Support |
| --- | ---: | ---: |
| running | 0.667 | 32 |
| walking | 0.687 | 32 |
| jumping | 0.316 | 32 |
| squatting | 0.436 | 32 |
| arm_wave | 0.522 | 32 |
| turning | 0.537 | 32 |
| falling | 0.605 | 32 |

## Test per-class F1 (`cross_user`)

| Class | F1 | Support |
| --- | ---: | ---: |
| running | 0.660 | 40 |
| walking | 0.271 | 40 |
| jumping | 0.148 | 40 |
| squatting | 0.272 | 40 |
| arm_wave | 0.512 | 40 |
| turning | 0.405 | 40 |
| falling | 0.513 | 40 |

## Test per-class F1 (`cross_environment`)

| Class | F1 | Support |
| --- | ---: | ---: |
| running | 0.341 | 80 |
| walking | 0.378 | 80 |
| jumping | 0.201 | 80 |
| squatting | 0.135 | 80 |
| arm_wave | 0.068 | 80 |
| turning | 0.371 | 80 |
| falling | 0.301 | 80 |

Full confusion matrices and train/val breakdowns: `artifacts/v2_logreg/20261010T045500Z/<strategy>/metrics.json` and root `manifest.json`.

## Observations

- Train accuracy (~74–82%) exceeds test on all strategies; largest generalization gap on `cross_environment` (test accuracy 27.0%).
- Dynamic activities (jumping, squatting, arm_wave) are weakest under domain shift; falling often has higher recall but lower precision in held-out environments.
- Baseline is intentionally simple (635-D classical features + multinomial logistic regression, `C=1.0`); no hyperparameter search in this slice.

## Follow-on models

Random Forest, 1D CNN, and GRU are documented in `docs/v2-engine-build-guide.md` with separate `reports/v2_*_results.md` files. Simulator prediction wiring remains deferred (V3).
