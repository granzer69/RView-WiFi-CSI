# V2 GBDT baseline — measured results

Run: `20261012T140000Z` (artifacts under `artifacts/v2_gbdt/20261012T140000Z/`).  
Config: `configs/experiments/v2_gbdt_esp_fi.yaml`.  
Training: `python3 scripts/train_gbdt.py --run-id 20261012T140000Z`.

**Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 are **INFERRED — NOT INDEPENDENTLY VERIFIED**.

**Model:** sklearn `HistGradientBoostingClassifier` on `classical_v1` features; scaler fit on **train** only.

## Split verification

| Strategy | Assignment SHA-256 (locked) | Train | Val | Test |
| --- | --- | ---: | ---: | ---: |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` | 1792 | 224 | 224 |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` | 1680 | 280 | 280 |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` | 1120 | 560 | 560 |

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 | Model size (bytes) | Inference (ms/sample, mean) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `in_domain` | 0.7366 | 0.7367 | 0.7367 | 5222406 | 0.078 |
| `cross_user` | 0.4000 | 0.3791 | 0.3791 | 5053538 | 0.078 |
| `cross_environment` | 0.3196 | 0.3096 | 0.3096 | 4269317 | 0.078 |

## Comparison to random forest (test macro-F1)

| Strategy | GBDT | Random Forest |
| --- | ---: | ---: |
| `in_domain` | 0.7367 | **0.7668** |
| `cross_user` | **0.3791** | 0.3349 |
| `cross_environment` | **0.3096** | 0.2912 |

GBDT is the strongest measured model on **cross-user** and **cross-environment** test macro-F1 among tree/boosting and classical baselines in this ladder (logreg cross-user: 0.3974).

**Thesis ladder:** `docs/thesis-benchmark-ladder.md`
