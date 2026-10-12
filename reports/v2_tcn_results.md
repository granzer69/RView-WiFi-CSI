# V2 TCN baseline — results status

**Config:** `configs/experiments/v2_tcn_esp_fi.yaml`  
**Training entry:** `scripts/train_tcn.py`  
**Artifacts root:** `artifacts/v2_tcn/<run_id>/<strategy>/`

## Status: not measured in this repository snapshot

Full ESP-Fi training was **not executed** on the 2026-10-12 benchmark VM because `data/raw/esp-fi-har/` is missing. No `artifacts/v2_tcn/` run is checked in yet.

## Intended protocol (same as CNN / GRU)

| Strategy | Assignment SHA-256 (locked) |
| --- | --- |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` |

**Labels:** `published_folder_codes_not_readme`; scenarios 1, 2, 4 **INFERRED — NOT INDEPENDENTLY VERIFIED**.

**Model:** Temporal convolution network on raw amplitude `(52, 950)` channels-first; train-only amplitude normalizer; PyTorch weights in `model.pt`.

## Reproduce

```bash
python3 scripts/train_tcn.py --run-id 20261012T120000Z
```

Pin `EXTENDED_RUN_IDS["tcn"]`, export JSON for the UI, then fill the table below from artifacts.

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 | Model size | Inference (ms/sample) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `in_domain` | *pending* | *pending* | *pending* | *pending* | *pending* |
| `cross_user` | *pending* | *pending* | *pending* | *pending* | *pending* |
| `cross_environment` | *pending* | *pending* | *pending* | *pending* | *pending* |

**Thesis ladder:** `docs/thesis-benchmark-ladder.md`
