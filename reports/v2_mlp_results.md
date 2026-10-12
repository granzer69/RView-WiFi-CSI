# V2 MLP baseline — measured results

Run: `20261012T140000Z` (artifacts under `artifacts/v2_mlp/20261012T140000Z/`).  
Config: `configs/experiments/v2_mlp_esp_fi.yaml`.  
Training: `python3 scripts/train_mlp.py --run-id 20261012T140000Z`.

**Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 are **INFERRED — NOT INDEPENDENTLY VERIFIED** (see manifest `label_note`).

**Model:** sklearn `MLPClassifier` on `classical_v1` features; scaler fit on **train** only.

## Split verification

| Strategy | Assignment SHA-256 (locked) | Train | Val | Test |
| --- | --- | ---: | ---: | ---: |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` | 1792 | 224 | 224 |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` | 1680 | 280 | 280 |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` | 1120 | 560 | 560 |

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 | Model size (bytes) | Inference (ms/sample, mean) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `in_domain` | 0.6384 | 0.6290 | 0.6290 | 2196446 | 0.002 |
| `cross_user` | 0.3000 | 0.2812 | 0.2812 | 2197482 | 0.002 |
| `cross_environment` | 0.2875 | 0.2748 | 0.2748 | 2196138 | 0.002 |

## Comparison to random forest (test macro-F1)

| Strategy | MLP | Random Forest |
| --- | ---: | ---: |
| `in_domain` | 0.6290 | **0.7668** |
| `cross_user` | 0.2812 | **0.3349** |
| `cross_environment` | 0.2748 | **0.2912** |

**Thesis ladder:** `docs/thesis-benchmark-ladder.md`
