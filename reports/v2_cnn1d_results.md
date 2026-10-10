# V2 1D CNN — measured results

Run: `20261010T070000Z` (artifacts under `artifacts/v2_cnn1d/20261010T070000Z/`).  
Config: `configs/experiments/v2_cnn1d_esp_fi.yaml`.  
Build guide: `docs/v2-engine-build-guide.md`.

**Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 are **INFERRED — NOT INDEPENDENTLY VERIFIED**.

**Input:** Raw amplitude `(950, 52)` → train-only per-subcarrier normalization → tensor `(52, 950)` for Conv1d.  
**Training:** 6 epochs, batch 32, Adam `lr=1e-3`, CPU.

## Split verification

Same locked assignment hashes and counts as `reports/v2_logreg_results.md`.

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 |
| --- | ---: | ---: | ---: |
| `in_domain` | 0.4688 | 0.4414 | 0.4414 |
| `cross_user` | 0.2286 | 0.2263 | 0.2263 |
| `cross_environment` | 0.2607 | 0.2342 | 0.2342 |

Training wall time per strategy: in_domain 20s, cross_user 17s, cross_environment 13s.

## Observations

- With only six epochs and no hyperparameter search, the CNN underperforms random forest on `in_domain` but is in the same ballpark as logreg on shift splits.
- Further tuning (epochs, learning rate, architecture) is explicitly out of scope for this baseline slice.

Artifacts: `artifacts/v2_cnn1d/20261010T070000Z/<strategy>/metrics.json`.
