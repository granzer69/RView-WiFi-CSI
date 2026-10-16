# V2 TCN baseline — measured results

Run: `20261012T140000Z` (artifacts under `artifacts/v2_tcn/20261012T140000Z/`).  
Config: `configs/experiments/v2_tcn_esp_fi.yaml`.  
Training: `python3 scripts/train_tcn.py --run-id 20261012T140000Z`.

**Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 are **INFERRED — NOT INDEPENDENTLY VERIFIED**.

**Model:** Temporal convolutional network on amplitude tensors; normalizer fit on **train** only.

## Split verification

| Strategy | Assignment SHA-256 (locked) | Train | Val | Test |
| --- | --- | ---: | ---: | ---: |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` | 1792 | 224 | 224 |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` | 1680 | 280 | 280 |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` | 1120 | 560 | 560 |

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 | Model size (bytes) | Inference (ms/sample, mean) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `in_domain` | 0.3125 | 0.3012 | 0.3012 | 169390 | 0.486 |
| `cross_user` | 0.1857 | 0.1575 | 0.1575 | 169393 | 0.486 |
| `cross_environment` | 0.1768 | 0.1708 | 0.1708 | 169400 | 0.486 |

## Observations

- Under default training budget in `v2_tcn_esp_fi.yaml`, TCN underperforms 1D CNN and GRU on this ladder; worth treating as a **capacity / hyperparameter** result rather than a negative result for conv-temporal architectures in general.

**Thesis ladder:** `docs/thesis-benchmark-ladder.md`
