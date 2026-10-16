# R-View Research Validity Audit

**Audit date:** 2026-10-11  
**Repository:** `granzer69/RView-WiFi-CSI`  
**Baseline commit audited:** `ebbfd301e3da06147e47d41982bb4b98aa322f19` (`main`)  
**Audit branch:** `feature/research-validity-audit`  
**Auditor role:** Code, artifact, export, UI, and test review (not a claim that pytest alone implies scientific validity).

---

## 1. Executive verdict

**PASS WITH LIMITATIONS**

Core holdout discipline is sound: session-grouped splits, test-only participant metrics, and personalization calibration/evaluation are separated by split and session ID. Generalization Lab numbers trace to frozen `metrics.json` artifacts with a consistent gap formula. No evidence of fabricated metrics, hardcoded performance in the Research Lab UI, or evaluation-label leakage into personalization fitting was found.

Limitations are primarily **interpretation and transparency**: the in-domain personalization A/B does not isolate a global model that never saw each participant’s training data; the Research Lab UI under-reports model coverage and label caveats; export provenance `git_sha` can lag `main`; and leakage safeguards are only partially covered by automated tests.

---

## 2. Repository baseline

| Check | Result |
| --- | --- |
| Branch at audit start | `main` @ `ebbfd30` |
| Working tree | Clean except untracked `internal/` (not part of product) |
| Audit branch | `feature/research-validity-audit` from `ebbfd30` |
| ESP-Fi data on audit VM | Present at `data/raw/esp-fi-har/` (local; not in git) |
| Baseline artifacts | Present under `artifacts/v2_{logreg,rf,cnn1d,gru}/<run_id>/<strategy>/` |
| Tests | `python3 -m pytest -q` → **61 passed**, 1 warning (~250 s) |
| Frontend build | `cd frontend && npm run build` → **success** |

Locked baseline run IDs (from `src/research/generalization.py`):

| Family | Run ID |
| --- | --- |
| logreg | `20261010T045500Z` |
| rf | `20261010T060000Z` |
| cnn1d | `20261010T070000Z` |
| gru | `20261010T080000Z` |

---

## 3. Findings summary

| ID | Severity | Area | Summary |
| --- | --- | --- | --- |
| F-01 | **High** | Personalization interpretation | Global baseline models were trained on the **full** in-domain train split, including each participant’s calibration sessions. Reported gains are **not** leave-one-user-out or unseen-user personalization. |
| F-02 | **High** | Personalization (logreg family) | For `family=logreg`, both arms use logistic regression on the same frozen features; the global arm’s weights already reflect that participant’s training labels. |
| F-03 | **Medium** | UI | User Profiling tab shows per-participant macro-F1 for **`model_metrics.models[0]` only** (logreg); rf/cnn1d/gru metrics exist in `participants.json` but are not shown. |
| F-04 | **Medium** | UI / labels | Research Lab does not surface the documented **INFERRED — NOT INDEPENDENTLY VERIFIED** label caveat for scenarios 1, 2, and 4 (see `docs/what-we-built.md`, training manifests). |
| F-05 | **Medium** | Provenance | `frontend/public/research/*.json` record `git_sha` `3f59fe…` while audit HEAD is `ebbfd30`; metrics match artifacts when re-read/recomputed. Re-export updates SHA only. |
| F-06 | **Medium** | Generalization metrics | When `macro_precision` / `macro_recall` are absent from `metrics.json`, `supplement_macro_averages()` fills them as the **unweighted mean of per-class** values in the report dict (usually aligned with sklearn when all seven classes appear). |
| F-07 | **Low** | Tests | Leakage tests cover a session-disjoint **helper** and count conservation, not an end-to-end assertion that every participant’s calib/eval session sets are disjoint in production exports. |
| F-08 | **Low** | Code hygiene | `calib_eval_session_sets_disjoint` is defined in `participant.py` and re-exported via `leakage.py` (duplicate definition). |

**Critical:** none identified in this audit.

---

## 4. Generalization Lab — metrics and provenance

### 4.1 Data flow

1. `scripts/export_research_lab.py` → `baseline_metrics_entries()` reads each `artifacts/v2_*/<run_id>/<strategy>/metrics.json`.
2. `build_generalization_rows()` attaches `in_domain_macro_f1` and `generalization_gap`.
3. UI/API: static `frontend/public/research/generalization.json` and `GET /research/generalization` (file passthrough in `src/api/main.py`).

### 4.2 Gap formula

```86:88:src/research/generalization.py
def compute_generalization_gap(in_domain_macro_f1: float, target_macro_f1: float) -> float:
    """Positive gap means in-domain test macro-F1 exceeds the target strategy."""
    return float(in_domain_macro_f1) - float(target_macro_f1)
```

- For each model **family**, in-domain test macro-F1 is the reference; gap for `cross_user` / `cross_environment` is `in_domain_macro_f1 - strategy_macro_f1`.
- In-domain rows correctly show gap **0** (same reference and target).
- **Spot check (RF):** artifact test macro-F1 `0.7668419869166858` matches `generalization.json`; `cross_user` gap ≈ `0.432` (`0.7668 - 0.3349`).

### 4.3 Metric definitions

- Training and export use `classification_report_dict()` in `src/evaluation/metrics.py` (sklearn `f1_score(..., average="macro")`, `zero_division=0`).
- Confusion matrices and per-class P/R/F1/support in artifacts use label order from `NORMALIZED_LABELS` / model `label_names`.
- Missing metrics in the UI gap table render as **—**, not zero (`ResearchLabPage.tsx` `GapTable`).

### 4.4 Historical vs generated

- Generalization numbers are **read-only** from frozen baseline artifacts (`integrity_note` in export payload).
- Participant and personalization JSON are **regenerated** by `scripts/export_participant_profiles.py` when ESP-Fi is available; they are not taken from `metrics.json` alone.

---

## 5. Participant profiles — held-out validity

### 5.1 Methodology (verified)

```212:216:src/research/participant.py
        "methodology": (
            "Per-participant metrics use only sessions assigned to the test split. "
            "Predictions are regenerated from frozen baseline artifacts; train/val "
            "sessions are excluded."
        ),
```

- `_group_test_samples_by_user()` filters `sample.split == "test"` only.
- Overview counts: 8 users × (224 train, 28 val, 28 test) = 280 sessions/user, 2240 trials total — consistent with locked in-domain assignment.

### 5.2 Reproducibility check

- Recomputed logreg in-domain test macro-F1 for **user 1**: `0.6037414965986393` — **exact match** to `participants.json` and to personalization “general” arm for the same user/family.

### 5.3 Support

- Each participant has 28 test sessions and per-class support in full-dataset test metrics; per-user test sets are smaller (28 trials, not 28×7 balanced per class). Per-user macro-F1 can be high-variance for rare activities — expected, not a leakage defect.
- Train-set metrics exist inside `metrics.json` under `"train"` but are **not** shown in the Research Lab profiling tab.

---

## 6. Personalization A/B — leakage assessment (highest priority)

### 6.1 Protocol (as implemented)

Documented in `run_in_domain_personalization_ab()` (`src/research/personalization.py`):

| Step | Data | Labels used in fit? |
| --- | --- | --- |
| Global predictions | Participant **test** sessions | No (inference only) |
| Feature extraction | Frozen baseline extractor from artifact | No refit on test |
| Calibrator fit | Participant **train** sessions | Yes (train labels only) |
| Personalized predictions | Participant **test** sessions | No (inference only) |
| cross_user | Not run | **blocked** |

Session granularity: one `.mat` trial → one `HarSample` (`training/esp_fi.py` expects one window per trial). Split assignment is **per session_id**; train and test session sets for a participant are disjoint by construction.

### 6.2 Requirement checklist

| Requirement | Status | Evidence |
| --- | --- | --- |
| Calibration and evaluation trials independent | **Pass** | Train vs test split; runtime `calib_eval_session_sets_disjoint(calib_sessions, eval_sessions)` |
| No overlapping windows from same trial across boundary | **Pass** | One sample per `session_id`; split is session-level |
| Eval labels not used for fitting / tuning | **Pass** | `_fit_participant_calibrator(train_feat, train_y)`; `test_y` only in `classification_report_dict` |
| Preprocessing not refit on eval | **Pass** | `backend.features()` uses artifact-loaded extractor only |
| Same held-out examples for both arms | **Pass** | `general_pred` and `personalized_pred` on identical `test_x` / `test_y` |
| Counts, seed, coverage recorded | **Pass** | `calibration_session_count`, `evaluation_session_count`, `calibrator_seed: 42`, 8/8 participants |
| Improvement from actual predictions | **Pass** | Re-run `run_in_domain_personalization_ab(ROOT)` matched stored JSON (logreg mean Δ `0.176129`, user 1 Δ `0.207256`) |
| Not misrepresented as unseen-user personalization | **Partial** | `cross_user_personalization: blocked` and protocol text; **F-01** limitation now explicit in `limitations` string |

### 6.3 Non-leakage methodological limits (not failures)

- **F-01:** The frozen global classifier was trained on **all** in-domain training sessions, including participant *P*’s sessions, before the A/B comparison. This is standard for the chosen split but **must not** be read as “adapt to a user the global model has never seen.”
- **F-02:** For `family=logreg`, the personalized arm is a second logistic regression on the same features; comparison is still a fair same-test-set A/B, but the global arm is not a “cold” global model for that user.
- Validation sessions are **not** used for calibration (only train). Documented as design choice, not leakage.

### 6.4 Tests

- `tests/test_research_personalization.py`: integration run when data present; checks status, blocked cross_user, positive session counts.
- `tests/test_research_leakage.py`: helper disjointness; overview count sum — **does not** replace full per-user session-ID audit (**F-07**).

---

## 7. Reproducibility and integrity

| Item | Assessment |
| --- | --- |
| Regenerate generalization export | `python3 scripts/export_research_lab.py` — reads artifacts only; deterministic given artifacts |
| Regenerate participant + personalization | `python3 scripts/export_participant_profiles.py` — requires local ESP-Fi; personalization ~3 min on audit VM |
| Assignment integrity | `metrics.json` includes `assignment_sha256`; bundle loader can verify against `EXPECTED_ASSIGNMENT_SHA256` in `training/esp_fi.py` |
| Hardcoded Research metrics | **Not found** — values trace to artifacts or live recomputation |
| Raw gated data in git | **Not found** — data local only |
| Baseline artifact overwrite | Audit did not modify `artifacts/v2_*` |

**Export provenance note:** `generalization.json` / `participants.json` `git_sha` may be older than `ebbfd30` until re-export; numeric content was verified against artifacts and live recomputation at audit time.

---

## 8. UI and API transparency

| Surface | Source | Gaps |
| --- | --- | --- |
| `/research` Generalization tab | `generalization.json` | Shows `integrity_note`; gaps hidden for in-domain (correct) |
| User Profiling | `participants.json` | **F-03:** only first model family in UI |
| Personalization | `personalization.json` (static); no FastAPI route | Protocol, limitations, blocked cross_user shown |
| Experiment Details | `git_sha`, baseline run IDs | Does not show label-map caveat (**F-04**) |
| `/research/generalization`, `/research/participants` API | Read JSON from `frontend/public/research/` | 404 with hint to run export if missing |
| Replay / evaluation | Unchanged routes | Compatible; not altered by Research Lab |

---

## 9. Corrective actions (priority order)

1. **Done (minimal, this branch):** Extend `limitations` in `src/research/personalization.py` and `frontend/public/research/personalization.json` to state F-01/F-02 explicitly (no protocol change).
2. **Recommended:** Add Research Lab UI note for label inference caveat (link to `docs/what-we-built.md` or manifest `label_note`).
3. **Recommended:** User Profiling — family selector or list all four families from `model_metrics.models`.
4. **Recommended:** Add integration test asserting per-participant train/test `session_id` sets are disjoint under `in_domain` (stronger than count-only test).
5. **Optional:** Re-run `export_participant_profiles.py` and `export_research_lab.py` on release commits so `git_sha` matches `main`.
6. **Optional:** Remove duplicate `calib_eval_session_sets_disjoint` from `participant.py`; keep single definition in `research/leakage.py`.

---

## 10. Evidence index

| Topic | Primary paths |
| --- | --- |
| Generalization | `src/research/generalization.py`, `scripts/export_research_lab.py`, `frontend/public/research/generalization.json` |
| Participants | `src/research/participant.py`, `scripts/export_participant_profiles.py`, `frontend/public/research/participants.json` |
| Personalization | `src/research/personalization.py`, `src/research/leakage.py`, `frontend/public/research/personalization.json` |
| Metrics | `src/evaluation/metrics.py`, `artifacts/v2_*/**/metrics.json` |
| UI | `frontend/src/pages/ResearchLabPage.tsx` |
| API | `src/api/main.py` (`/research/generalization`, `/research/participants`) |
| Tests | `tests/test_research_generalization.py`, `tests/test_research_personalization.py`, `tests/test_research_leakage.py` |
| Label policy | `docs/what-we-built.md`, `src/training/experiment.py` (`label_map`) |

---

## 11. Audit branch changes

- Added this document: `docs/research-validity-audit.md`
- Clarified personalization `limitations` text (interpretation only; no change to splits, models, or artifacts)

**Not merged to `main`** per audit instructions.
