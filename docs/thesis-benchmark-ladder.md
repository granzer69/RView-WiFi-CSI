# Thesis benchmark ladder — ESP-Fi HAR (seven model families)

**Authoring context:** Final-year project (Ribhu S.), R-View WiFi CSI.  
**Evaluation protocol:** Session-grouped splits (`in_domain`, `cross_user`, `cross_environment`); locked assignment SHA-256 per strategy; test metrics only for headline comparisons.  
**Status (2026-10-12):** Four families have frozen measured runs in-repo; **MLP, GBDT, and TCN** are implemented and registered in the platform but **were not re-trained on this VM** because `data/raw/esp-fi-har/` is absent (see [Extended families blocker](#extended-families-blocker)).

---

## Executive summary (for examiners)

This project compares **seven** human-activity recognition models on the **same** ESP-Fi WiFi CSI dataset and **identical** leakage-safe splits: classical baselines (logistic regression, random forest, MLP, gradient-boosted trees), and deep models on raw amplitude tensors (1D CNN, GRU, TCN). The honest headline is that **no single model wins every generalization axis**. Random forest achieves the best **in-domain** test macro-F1 (~0.77) but drops sharply on **cross-user** holdout (~0.33), where **logistic regression** is strongest among measured runs (~0.40). Deep models under the default full-trial preprocess trail RF on in-domain performance; GRU is weakest on this ladder. Cross-user evaluation is the hardest axis for every family measured so far.

The software platform exports these metrics into the **Evaluation** and **Research Lab** views from `artifacts/v2_*/<run_id>/<strategy>/metrics.json` — numbers are never hard-coded in the UI. Label uncertainty for scenarios without class folders and limitations of offline personalization are documented below and in `docs/generalization-user-profiling-audit.md`.

**Recommended thesis narrative:** Present the ladder as a **fair comparison under fixed splits**, discuss **generalization gaps** (in-domain minus cross-user macro-F1), and treat MLP/GBDT/TCN as **architectural extensions** whose metrics should be filled from a single shared training run once ESP-Fi is available locally.

---

## Master results table (test set)

Macro-F1 and accuracy from frozen baselines unless noted. **Cross-user gap** = in-domain test macro-F1 minus cross-user test macro-F1 (higher = more drop when users change).

| Family | Run ID | In-domain acc | In-domain macro-F1 | Cross-user acc | Cross-user macro-F1 | Cross-env acc | Cross-env macro-F1 | Cross-user gap |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Random forest | `20261010T060000Z` | 0.768 | **0.767** | 0.350 | 0.335 | 0.298 | **0.291** | 0.432 |
| Logistic regression | `20261010T045500Z` | 0.545 | 0.539 | 0.429 | **0.397** | 0.270 | 0.256 | 0.141 |
| 1D CNN | `20261010T070000Z` | 0.469 | 0.441 | 0.229 | 0.226 | 0.261 | 0.234 | 0.215 |
| GRU | `20261010T080000Z` | 0.241 | 0.213 | 0.218 | 0.132 | 0.195 | 0.178 | 0.081 |
| MLP | *pending* | — | — | — | — | — | — | — |
| GBDT | *pending* | — | — | — | — | — | — | — |
| TCN | *pending* | — | — | — | — | — | — | — |

### Which model wins which axis (measured families only)

| Axis | Winner (macro-F1) | Value | Runner-up |
| --- | --- | ---: | --- |
| In-domain | Random forest | 0.767 | Logistic regression (0.539) |
| Cross-user | Logistic regression | 0.397 | Random forest (0.335) |
| Cross-environment | Random forest | 0.291 | 1D CNN (0.234) |
| Smallest cross-user gap | GRU | 0.081 | Logistic regression (0.141) |

RF memorizes training sessions (100% train accuracy in reports) yet still leads in-domain; **cross-user** remains the thesis-critical failure mode for deployment to new participants.

---

## Label uncertainty caveat

Activity labels use `published_folder_codes_not_readme` (scenario 3 folder layout), **not** the ESP-Fi README code table (codes 2–7 disagree; only “run” aligns). Scenarios **1, 2, and 4** lack per-class folders in the extracted tree; labels there are **INFERRED — NOT INDEPENDENTLY VERIFIED** and recorded in each run `manifest.json` / `label_note`. Report headline metrics with this caveat; per-scenario analysis should treat scenario 3 as the most reliable label source.

---

## Personalization and generalization limitations

Offline evaluation does **not** prove live-room or live-user performance. The Research Lab’s participant and personalization views depend on the same held-out splits and optional regeneration of test predictions — see **Phase 0 audit** (`docs/generalization-user-profiling-audit.md`): per-trial predictions are not persisted in artifacts; participant-level metrics require reloading frozen models on the test split. **In-domain personalization A/B** in the UI compares strategies within the same user cohort — it does not replace cross-user validation. For examiners: emphasize **session-grouped splits** as the validity backbone; treat UI personalization as exploratory.

---

## Extended families blocker

| Item | Detail |
| --- | --- |
| Required data | Extracted ESP-Fi HAR under `data/raw/esp-fi-har/` (gitignored) |
| This VM (2026-10-12) | **Not present** — training skipped; no fabricated metrics |
| Code readiness | `scripts/train_mlp.py`, `train_gbdt.py`, `train_tcn.py`; configs `configs/experiments/v2_*_esp_fi.yaml` |
| Research export | `extended_metrics_entries()` in `src/research/generalization.py`; pin runs via `EXTENDED_RUN_IDS` after training |
| Per-family reports | `reports/v2_mlp_results.md`, `v2_gbdt_results.md`, `v2_tcn_results.md` (blocker + reproduce commands) |

**Suggested shared run ID after training:** `20261012T120000Z` (use a fresh UTC timestamp if that directory already exists).

---

## How to reproduce

### Prerequisites

1. Clone repo and install Python deps (`pip install -e .` per `docs/SETUP.md`).
2. Extract ESP-Fi into `data/raw/esp-fi-har/` (see `data/README.md`).
3. Verify splits: training scripts assert `assignment_sha256` against `src/training/esp_fi.py` → `EXPECTED_ASSIGNMENT_SHA256`.

### Frozen baselines (already in repo — do not overwrite)

| Family | Run ID |
| --- | --- |
| logreg | `20261010T045500Z` |
| rf | `20261010T060000Z` |
| cnn1d | `20261010T070000Z` |
| gru | `20261010T080000Z` |

### Train extended families (one run ID for all three strategies each)

```bash
export RUN_ID=20261012T120000Z
python3 scripts/train_mlp.py --run-id "$RUN_ID"
python3 scripts/train_gbdt.py --run-id "$RUN_ID"
python3 scripts/train_tcn.py --run-id "$RUN_ID"
```

Then pin in `src/research/generalization.py`:

```python
EXTENDED_RUN_IDS = {
    "mlp": "20261012T120000Z",
    "gbdt": "20261012T120000Z",
    "tcn": "20261012T120000Z",
}
```

### Export for UI / thesis tables

```bash
python3 scripts/export_evaluation_summary.py
python3 scripts/export_research_lab.py
python3 scripts/plot_generalization_gaps.py --out reports/figures/generalization_gaps.png
```

### Locked assignment hashes (all families)

| Strategy | SHA-256 |
| --- | --- |
| `in_domain` | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` |
| `cross_user` | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` |
| `cross_environment` | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` |

---

## Figure suggestions

1. **Confusion matrix** — export from `metrics.json` → `test.confusion_matrix` for RF in-domain vs cross-user (contrast diagonal collapse).
2. **Generalization gap bar chart** — `scripts/plot_generalization_gaps.py` (macro-F1 by family, grouped by split).
3. **Per-class F1 heatmap** — optional; per-class blocks exist in each `metrics.json`.

---

## Related documents

| Document | Role |
| --- | --- |
| `docs/what-we-built.md` | Platform narrative and headline metrics |
| `reports/v2_*_results.md` | Per-family measured tables |
| `docs/v2-engine-build-guide.md` | Training and artifact layout |
| `docs/research-lab-methodology.md` | Generalization gap definitions |
| `docs/generalization-user-profiling-audit.md` | Validity and personalization limits |
