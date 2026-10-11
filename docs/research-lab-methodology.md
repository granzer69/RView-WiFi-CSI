# Research Lab methodology

## Generalization Lab

- **Sources:** Frozen baseline artifacts only (`artifacts/v2_<family>/<run_id>/<strategy>/metrics.json`). Baseline run IDs are locked in `src/research/generalization.py`.
- **Gap formula:** `generalization_gap = in_domain_test_macro_f1 - target_strategy_test_macro_f1` for the same model family. Positive gaps indicate in-domain performance exceeds the target split.
- **Confused pairs:** Off-diagonal entries from the test confusion matrix, sorted by count (top 10 per model).
- **Macro precision/recall:** Taken from `metrics.json` when present; otherwise averaged from per-class precision/recall in the export scripts.

## User Profiling Lab

- **Metadata:** `discover_trials` + `assign_splits` (seed 42) produce per-participant train/val/test session counts.
- **Per-participant metrics:** Load each frozen model, predict **only** `test` split sessions, aggregate metrics with `classification_report_dict`, grouped by `user_id`.
- **Blocked state:** When `data/raw/esp-fi-har` is missing, exports return `status: blocked` with a reason string.

## Personalization (documented, not fully evaluated)

- **In-domain protocol:** Calibrate on each participant's **train** sessions; evaluate on that participant's **test** sessions (session-disjoint).
- **cross_user:** Personalization blocked — held-out users do not appear in training.
- **Export status:** `personalization.json` uses `not_evaluated` until an A/B personalization script is implemented.

## Leakage rules

- Never score train or val sessions in participant profiling exports.
- Calibration and evaluation session ID sets must be disjoint (`calib_eval_session_sets_disjoint`).
- Do not change split hashes, seeds, or label maps without approval.
