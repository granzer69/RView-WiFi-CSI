# V2 random forest baseline — measured results

Run: `20261010T060000Z` (artifacts under `artifacts/v2_rf/20261010T060000Z/`).  
Config: `configs/experiments/v2_rf_esp_fi.yaml`.  
Build guide: `docs/v2-engine-build-guide.md`.

**Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 are **INFERRED — NOT INDEPENDENTLY VERIFIED** (see manifest `label_note`).

**Preprocessing:** V1 default (validate only, one full trial, no global z-score). Classical feature scaler fit on **train** only. Random forest: `n_estimators=200`, `max_depth=null`.

## Split verification

| Strategy | Assignment SHA-256 (locked) | Train | Val | Test |
| --- | --- | ---: | ---: | ---: |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` | 1792 | 224 | 224 |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` | 1680 | 280 | 280 |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` | 1120 | 560 | 560 |

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 | Model size (bytes) | Inference (ms/sample, mean) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `in_domain` | 0.7679 | 0.7668 | 0.7668 | 17378487 | 0.104 |
| `cross_user` | 0.3500 | 0.3349 | 0.3349 | 15934675 | 0.112 |
| `cross_environment` | 0.2982 | 0.2912 | 0.2912 | 10353446 | 0.048 |

Training wall time per strategy (includes full ESP-Fi load + feature extraction): in_domain 260s, cross_user 253s, cross_environment 229s.

## Comparison to logistic regression (test macro-F1)

| Strategy | LogReg | Random Forest |
| --- | ---: | ---: |
| `in_domain` | 0.5385 | **0.7668** |
| `cross_user` | 0.3974 | 0.3349 |
| `cross_environment` | 0.2564 | **0.2912** |

LogReg reference: `reports/v2_logreg_results.md` (`20261010T045500Z`).

## Observations

- Random forest reaches **100% train accuracy** on all strategies (memorization capacity); test macro-F1 still improves over logreg on `in_domain` and `cross_environment`.
- `cross_user` test macro-F1 is slightly below logreg — held-out users remain the hardest axis for both classical models.
- Inference latency is ~100× slower than logreg due to tree ensemble size; artifact size is ~170 MB vs ~61 KB for logreg.

Full confusion matrices and train/val breakdowns: `artifacts/v2_rf/20261010T060000Z/<strategy>/metrics.json` and root `manifest.json`.
