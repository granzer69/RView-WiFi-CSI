# Thesis contributions — R-View WiFi CSI

**Project:** R-View — software-first Wi-Fi CSI human activity recognition on ESP-Fi HAR  
**Scope:** offline training, frozen artifacts, dataset replay demo — **no live hardware claims**

---

## Problem statement

Wi-Fi **channel state information (CSI)** can support human activity recognition (HAR) without body-worn sensors, but published results are hard to compare when splits leak sessions across train/test, labels disagree across dataset documentation, and UIs show numbers that are not tied to reproducible artifacts. This project delivers an **end-to-end, leakage-aware pipeline** and **interactive studio** that makes splits, models, and metrics inspectable.

---

## Evaluation protocol (splits)

Three **session-grouped** strategies on ESP-Fi HAR:

| Strategy | Intent |
| --- | --- |
| `in_domain` | Random session holdout within the same user/environment mix |
| `cross_user` | Hold out entire participants — deployment-critical generalization |
| `cross_environment` | Hold out environment folders — room/geometry shift |

Each strategy has a **locked assignment SHA-256** verified during training and recorded in `metrics.json` / manifests. The published ESP-Fi `train_amp` / `test_amp` folders are documented separately as a **leakage check**, not the headline thesis split (see [`research-validity-audit.md`](research-validity-audit.md)).

---

## Model families (seven)

| # | Family | Artifact prefix | Measured in-repo (frozen run) |
| --- | --- | --- | --- |
| 1 | Logistic regression | `v2_logreg` | Yes — `20261010T045500Z` |
| 2 | Random forest | `v2_rf` | Yes — `20261010T060000Z` |
| 3 | MLP | `v2_mlp` | Code + configs; metrics pending ESP-Fi retrain |
| 4 | Gradient-boosted trees (GBDT) | `v2_gbdt` | Code + configs; metrics pending ESP-Fi retrain |
| 5 | 1D CNN | `v2_cnn1d` | Yes — `20261010T070000Z` |
| 6 | GRU | `v2_gru` | Yes — `20261010T080000Z` |
| 7 | TCN | `v2_tcn` | Code + configs; metrics pending ESP-Fi retrain |

All families share the **same** split assignments and preprocessing defaults for fair comparison. Deep and extended families use **baseline hyperparameters** from YAML — not a full search (limitation).

---

## Benchmark headline results (test macro-F1)

Source: [`thesis-benchmark-ladder.md`](thesis-benchmark-ladder.md) — frozen `artifacts/v2_*/**/metrics.json`.

| Family | In-domain macro-F1 | Cross-user macro-F1 | Cross-env macro-F1 |
| --- | ---: | ---: | ---: |
| Random forest | **0.767** | 0.335 | **0.291** |
| Logistic regression | 0.539 | **0.397** | 0.256 |
| 1D CNN | 0.441 | 0.226 | 0.234 |
| GRU | 0.213 | 0.132 | 0.178 |

**Headline narrative:** No model wins every axis. RF is strongest **in-domain** and **cross-environment** among measured runs; **logistic regression** is strongest on **cross-user** holdout. **Cross-user** is the hardest deployment axis for every measured family. MLP, GBDT, and TCN slots are reserved for the same protocol once trained on a machine with ESP-Fi extracted.

**Label caveat:** Scenarios 1, 2, and 4 use **inferred** labels; scenario 3 uses folder layout. Report metrics with this uncertainty (see ladder § Label uncertainty).

---

## Software contributions

1. **Canonical CSI window** and ESP-Fi ingestion with integrity metadata (`data/metadata/esp-fi-har.json`).
2. **Training engine** with split verification, classical + deep baselines, and export to `artifacts/v2_*`.
3. **FastAPI platform** — health, model registry, predictions, optional WebSocket replay from `RVIEW_DATA_ROOT`.
4. **Sensing Studio UI** — dataset replay, activity views, model picker, evaluation dashboard, research lab exports (`frontend/public/evaluation/summary.json`, `frontend/public/research/*.json`).
5. **Validity documentation** — research audit, benchmark ladder, strengths/limitations, smoke test, CI (`pytest` + frontend build).

---

## Limitations (examiner-facing summary)

Full list: [`thesis-strengths-limitations.md`](thesis-strengths-limitations.md).

- Single corpus (ESP-Fi) for reported benchmark numbers.  
- Label map disagreements; non–scenario-3 labels not independently verified.  
- Offline evaluation and replay — not live room sensing or device heterogeneity.  
- Personalization views are **in-domain** exploratory calibration, not cold-start users.  
- Extended deep/ML families intentionally **under-tuned** relative to industrial HPO.

---

## Future work

| Item | Status |
| --- | --- |
| **Leave-one-user-out (LOUO)** | In progress — new split definition + locked hash, eval manifests, `docs/louo-evaluation.md` (sibling workstream; does not replace `cross_user` random holdout) |
| Train **MLP / GBDT / TCN** on shared run ID | Blocked only by local ESP-Fi extract; scripts ready |
| CSI-Bench / additional corpora | Out of current thesis ladder (license / acquisition) |
| Live ESP32 CSI capture | Explicitly out of scope for this defense build |

---

## How to reproduce (minimal)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ml]"
python3 -m pytest -q          # ESP-Fi integration tests skip if data absent
cd frontend && npm ci && npm run build
bash scripts/dev-stack.sh start-preview
```

With ESP-Fi at `data/raw/esp-fi-har/`: retrain extended families per [`thesis-benchmark-ladder.md`](thesis-benchmark-ladder.md) — **do not overwrite** frozen `20261010T*` run directories.

---

## Document index

| Doc | Role |
| --- | --- |
| [`thesis-benchmark-ladder.md`](thesis-benchmark-ladder.md) | Full results table + reproduce commands |
| [`research-validity-audit.md`](research-validity-audit.md) | Audit findings and PASS WITH LIMITATIONS |
| [`thesis-strengths-limitations.md`](thesis-strengths-limitations.md) | Viva sound bites |
| [`viva-demo-script.md`](viva-demo-script.md) | 15-minute demo path |
| [`smoke-test.md`](smoke-test.md) | Pre-defense acceptance checklist |
