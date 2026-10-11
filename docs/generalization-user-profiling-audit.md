# Generalization Lab + User Profiling Lab — Phase 0 audit

**Date:** 2026-10-11  
**Baseline:** `main` @ `75ddf3a` (Sensing Studio UI merged)  
**Feature branch:** `feature/generalization-user-profiling`  
**Repository:** `granzer69/RView-WiFi-CSI`

## 1. Git and environment

| Item | Value |
| --- | --- |
| HEAD (audit start) | `75ddf3a7ead36bea4089bea20d97b3749f860952` |
| Remotes | `rview` → GitHub; `origin` → Cursor mirror |
| Baseline tests | **47** collected (`pytest`) |
| ESP-Fi on agent VM | Present under `data/raw/esp-fi-har/` (not in git) |

## 2. Data model (verified)

| Concept | Representation |
| --- | --- |
| Trial / session | One `.mat` file; `session_id` = stem `user-scenario-activity-trial` (e.g. `1-1-2-1`) |
| Participant | `participant_id` / `user_id` int 1–8 from filename |
| Scenario | `scenario_id` 1–4 (`environment_id`) |
| Activity | `label_id` 1–7; normalized string via `published_folder_codes_not_readme` |
| Split unit | **Session** — never split a trial across train/val/test |
| Strategies | `in_domain`, `cross_user`, `cross_environment` (seed 42, 15% val/test) |
| Locked hashes | `src/training/esp_fi.py` → `EXPECTED_ASSIGNMENT_SHA256` |

**Important:** One session = one trial = one matrix (950×52). No multi-window trials in default preprocess.

## 3. Metrics provenance

| Source | Contents |
| --- | --- |
| `artifacts/v2_*/<run_id>/<strategy>/metrics.json` | Full train/val/**test** metrics: accuracy, macro/weighted F1, **per_class P/R/F1/support**, confusion matrix, assignment SHA, counts |
| `scripts/export_evaluation_summary.py` | Aggregates to `frontend/public/evaluation/summary.json` — **currently drops** macro precision/recall; exports only `per_class_f1` map |
| Training | `classification_report_dict` in `src/evaluation/metrics.py` (sklearn, zero_division=0) |

**Per-trial predictions:** Not persisted in artifacts today. Participant-level metrics require **regenerating** test-set predictions (load frozen model + `load_esp_fi_split_bundle` test split) — feasible without retraining.

## 4. Models and artifacts (baseline — do not overwrite)

| Family | Run ID | Path pattern |
| --- | --- | --- |
| logreg | `20261010T045500Z` | `artifacts/v2_logreg/...` |
| rf | `20261010T060000Z` | `artifacts/v2_rf/...` |
| cnn1d | `20261010T070000Z` | `artifacts/v2_cnn1d/...` |
| gru | `20261010T080000Z` | `artifacts/v2_gru/...` |

## 5. Backend / frontend (touch points)

| Area | Files |
| --- | --- |
| API | `src/api/main.py`, `model_registry.py` — no research routes yet |
| WS | `src/api/replay_stream.py` — unchanged scope |
| UI routes | `/`, `/evaluation` — add `/research/*` under `WorkspaceShell` |
| Design | `index.css`, `WorkspaceShell`, cards/badges |

## 6. Leakage risks

| Risk | Mitigation |
| --- | --- |
| Scaler/normalizer on test | Existing training fits on train only — preserve in any new export script |
| Participant profiling on train predictions | Export script must filter **`split == test`** only |
| Personalization calib vs eval | **Same session** cannot appear in both; **same trial** has one session |
| cross_user test users | Not in training set — global model only; calib from test partition would leak labels into adaptation if eval is same sessions |
| Window-level random split | **Forbidden** — not used |

## 7. Feasible experiments (this iteration)

| Feature | Feasibility |
| --- | --- |
| Generalization Lab (gaps, full metrics, confusion) | **Yes** — from `metrics.json` + exporter |
| Richer evaluation JSON + API/static | **Yes** |
| Per-class P/R in UI | **Yes** — data already in metrics.json |
| Participant overview (metadata counts) | **Yes** — from `discover_trials` + split assignment |
| Participant test metrics per model | **Yes** — regenerate predictions on test sessions only |
| Confused pairs | **Yes** — derive from confusion matrix |
| Personalization A/B | **Partial** — defensible protocol only for **in_domain**: calib = participant's **train** sessions, eval = participant's **test** sessions; compare frozen global classifier vs participant-specific calibration (e.g. temperature or logreg on train features). **cross_user** personalization: **blocked** (test users absent from train; no non-test calib without protocol change). |

## 8. Blockers

| Blocker | Impact |
| --- | --- |
| No ESP-Fi on disk | Participant prediction export skipped; UI shows blocked + metadata-only profiles |
| CSI-Bench / Embedded | Out of scope (gated) |

## 9. Implementation boundaries (approved without further sign-off)

- New package `src/research/` (metrics, gaps, participant aggregation, experiment record types)
- New scripts under `scripts/export_research_*.py` writing to `frontend/public/research/` and `reports/research/` (not overwriting `reports/v2_*` or baseline artifacts)
- Extend `export_evaluation_summary.py` (additive fields)
- Optional read-only FastAPI routes serving static research JSON (no WS changes)
- Frontend `ResearchLabPage` + subviews
- Tests for metrics/gaps/leakage helpers
- Docs: methodology + build guide

## 10. Requires approval before implementation

- Changing split seed, assignment hashes, or label map
- New training runs overwriting baseline artifacts
- Personalization method beyond documented in-domain session-disjoint protocol
- Breaking API/WS changes
- Database / experiment tracking service

## 11. Proposed deliverables

1. `scripts/export_research_lab.py` — generalization manifest + gaps + experiment provenance  
2. `scripts/export_participant_profiles.py` — test-only per-participant metrics (if data present)  
3. `frontend/public/research/*.json`  
4. `docs/research-lab-methodology.md`, `docs/research-lab-build-guide.md`  
5. `frontend/src/pages/ResearchLabPage.tsx` (+ components)  
6. `tests/test_research_*.py`  
7. Personalization section: **status: not_evaluated** with protocol text until script lands
