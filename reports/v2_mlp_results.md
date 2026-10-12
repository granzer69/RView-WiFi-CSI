# V2 MLP baseline — results status

**Config:** `configs/experiments/v2_mlp_esp_fi.yaml`  
**Training entry:** `scripts/train_mlp.py`  
**Artifacts root:** `artifacts/v2_mlp/<run_id>/<strategy>/`

## Status: not measured in this repository snapshot

Full ESP-Fi training was **not executed** on the 2026-10-12 benchmark VM because `data/raw/esp-fi-har/` is missing (dataset is gitignored). No `artifacts/v2_mlp/` run is checked in yet. **Do not invent metrics** — run training locally and update this file from `metrics.json`.

## Intended protocol (same as RF / logreg)

| Strategy | Assignment SHA-256 (locked) | Expected train / val / test counts |
| --- | --- | ---: |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` | 1792 / 224 / 224 |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` | 1680 / 280 / 280 |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` | 1120 / 560 / 560 |

**Labels:** `published_folder_codes_not_readme`; scenarios 1, 2, 4 **INFERRED — NOT INDEPENDENTLY VERIFIED**.

**Model:** sklearn `MLPClassifier` on `classical_v1` features (635-D); scaler fit on train only. See config for `hidden_layer_sizes`, `max_iter`, `random_state`.

## Reproduce

```bash
python3 scripts/train_mlp.py --run-id 20261012T120000Z
```

After training, pin `EXTENDED_RUN_IDS["mlp"]` in `src/research/generalization.py`, run `export_evaluation_summary.py` and `export_research_lab.py`, and replace the section below with measured headline metrics (mirror `reports/v2_rf_results.md`).

## Test-set headline metrics

| Strategy | Accuracy | Macro-F1 | Weighted-F1 | Model size | Inference (ms/sample) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `in_domain` | *pending* | *pending* | *pending* | *pending* | *pending* |
| `cross_user` | *pending* | *pending* | *pending* | *pending* | *pending* |
| `cross_environment` | *pending* | *pending* | *pending* | *pending* | *pending* |

**Thesis ladder:** `docs/thesis-benchmark-ladder.md`
