# V2 GRU — measured results

Run: `20261010T080000Z` (artifacts under `artifacts/v2_gru/20261010T080000Z/`).  
Config: `configs/experiments/v2_gru_esp_fi.yaml`.  
Build guide: `docs/v2-engine-build-guide.md`.

**Labels:** `published_folder_codes_not_readme`. Scenarios 1, 2, and 4 are **INFERRED — NOT INDEPENDENTLY VERIFIED**.

**Input:** Raw amplitude `(950, 52)` time-major after train-only `AmplitudeNormalizer`.  
**Training:** 6 epochs, batch 32, Adam `lr=1e-3`, hidden size 64, CPU.

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 |
| --- | ---: | ---: | ---: |
| `in_domain` | 0.2143 | 0.2126 | 0.2126 |
| `cross_user` | 0.1357 | 0.1315 | 0.1315 |
| `cross_environment` | 0.1839 | 0.1777 | 0.1777 |

Training wall time per strategy: see `metrics.json` per strategy folder.

## Observations

- This shallow GRU baseline with minimal training does not yet beat classical models; it establishes the sequence contract and artifact path for later tuning.
- Sequence length 950 may benefit from downsampling or bidirectional layers in future work (not in this slice).

Artifacts: `artifacts/v2_gru/20261010T080000Z/<strategy>/metrics.json`.
