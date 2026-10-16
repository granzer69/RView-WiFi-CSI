# Leave-one-user-out (LOUO) evaluation — ESP-Fi HAR

LOUO complements the frozen **v2** holdout strategies (`in_domain`, `cross_user`, `cross_environment`). It does **not** replace them and does **not** overwrite artifacts under `artifacts/v2_*/20261010T*` or `20261012T*`.

## Protocol

| Item | Definition |
| --- | --- |
| Split unit | **Participant id** — all sessions from one user stay in the same partition |
| Folds | Eight folds: held-out test user = 1 … 8 |
| Train / val | Remaining seven users: **one** validation user (`max(1, floor(7 × 0.15))`), six training users |
| RNG | `numpy.random.Generator(seed + held_out_participant)` for val-user draw among the seven |
| Locked hashes | `configs/experiments/esp_fi_louo_splits.json` |

Compared with **`cross_user`**: that strategy randomly assigns one test and one validation user among eight (single draw, seed 42). LOUO **fixes** the test user per fold and reports all eight held-out users, so macro performance is an average over every participant as the unseen user.

## Limitations (honest)

- **Label inference:** Scenarios 1, 2, and 4 have no published class folders; activity codes follow the scenario-3 folder map (same caveat as v2 baselines).
- **Amplitude-only:** Classical and deep v2 pipelines use `CSIamp` matrices only (no phase).
- **Small cohort:** Eight participants — LOUO variance is high; use mean ± spread across folds, not a single fold.
- **Not personalization:** Held-out users never appear in training; this measures **global** generalization, not per-user calibration.

## Commands

Prerequisites: ESP-Fi extracted at `data/raw/esp-fi-har` (see main README).

### One fold (fast smoke — logreg + RF)

```bash
python scripts/run_louo_eval.py --run-id dev_smoke --fold 1 --family logreg --family rf
```

### All eight folds (classical families)

```bash
python scripts/run_louo_eval.py --run-id 20261016T120000Z
```

Artifacts:

- `artifacts/louo/louo_logreg/<run_id>/user_<k>/metrics.json`
- `artifacts/louo/louo_rf/<run_id>/user_<k>/metrics.json`
- Per-family `manifest.json` at the run root

### Table + figure

```bash
python scripts/build_louo_report.py
```

Outputs under `artifacts/louo/reports/<timestamp>/` and `artifacts/louo/reports/latest/`.

### Research Lab export

```bash
python scripts/export_louo_research.py
```

Writes `frontend/public/research/louo.json` (labeled **leave_one_user_out**, separate from v2 `generalization.json`).

### Deep families (cnn1d, gru, …)

Reuse the same LOUO assignment via `load_esp_fi_louo_bundle` and the existing deep training entrypoints; wire `split_strategy=louo_user_<k>` in model config. Not run in the default classical manifest — extend `scripts/run_louo_eval.py` or add family-specific runners when GPU time is available.

## Tests

```bash
python -m pytest tests/test_louo_splits.py tests/test_louo_research.py -q
```

Locked assignment hashes and session-group integrity are enforced in CI even when ESP-Fi is absent (synthetic full grid).

## Metrics format

Per-fold `metrics.json` matches v2 layout: `split_strategy`, `assignment_sha256`, `counts`, `train` / `val` / `test` classification reports (accuracy, macro-F1, per-class, confusion matrix).
