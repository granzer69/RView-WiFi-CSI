# ESP-Fi official `train_amp` / `test_amp` vs R-View session-grouped splits

This note contrasts the **authors’ published folders** with the **evaluation protocol used for all R-View thesis metrics**. They answer different questions; R-View headline numbers always come from the three session-grouped strategies, not from `train_amp` / `test_amp`.

---

## Authors’ published split (upstream repository)

| Dimension | Authors’ `train_amp` / `test_amp` |
| --- | --- |
| **Scope** | Scenario **3** (boardroom) only |
| **Holdout unit** | **Participant 1** in `test_amp`; participants **2–8** in `train_amp` |
| **Files** | 490 train + 70 test amplitude matrices (per `data/README.md`) |
| **Preprocessing (typical in paper/repo)** | Per-trial or per-window **z-score** normalization on CSI amplitude |
| **Role in R-View** | **Leakage check only** — confirms no shared session IDs between folders; **not** used for benchmark ladder tables |
| **Labels** | Class-folder names in scenario 3 (disagree with README activity-id table except `run`) |

---

## R-View session-grouped strategies (primary evaluation)

| Dimension | `in_domain` | `cross_user` | `cross_environment` |
| --- | --- | --- | --- |
| **Holdout unit** | Session (trial stem) | Participant | Scenario (environment) |
| **Scenarios** | All **1–4** | All **1–4** | All **1–4** |
| **Split rule** | ~15% sessions held out per stratum; seed **42** | ~15% participants held out | ~15% scenarios held out |
| **Preprocessing (frozen V2 runs)** | Default validate-only full trial (`normalize: none`); classical models use **train-fit** feature scaler | Same per strategy | Same per strategy |
| **Integrity** | Locked `assignment_sha256` per strategy in `metrics.json` | Same | Same |
| **Thesis use** | In-domain macro-F1 and generalization **gaps** vs this reference | Cross-user generalization | Cross-environment generalization |

---

## Side-by-side protocol summary

| Question | Official `train_amp` / `test_amp` | R-View three strategies |
| --- | --- | --- |
| Can I compare to the paper’s scenario-3 participant holdout? | Yes, if you train with their normalization on those folders | Not directly — different units, scenarios, and preprocessing |
| Does it test new users in new rooms? | Only **one** held-out user in **one** room | `cross_user` and `cross_environment` stress different axes on the **full** grid |
| Used in Evaluation / Research Lab UI? | No (optional script below) | Yes — frozen `artifacts/v2_*/…/metrics.json` |
| Label caveat for scenarios 1/2/4 | N/A (scenario 3 only) | Inferred labels — see `docs/what-we-built.md` |

---

## Optional: reproduce official-folder macro-F1 locally

If extracted ESP-Fi contains `train_amp` and `test_amp` under the data root (typically under scenario 3), run:

```bash
python3 scripts/compare_official_esp_fi_pack.py --family rf
# or: --family logreg
```

The script:

1. Locates `**/train_amp/mat/*.mat` and `**/test_amp/mat/*.mat` under `data/raw/esp-fi-har/`.
2. Skips gracefully with a clear message if either folder is missing (**no fabricated numbers**).
3. Applies **per-subcarrier z-score** fit on `train_amp` only (closer to common ESP-Fi practice than R-View’s default full-trial export).
4. Trains a **fresh** random forest or logistic regression with hyperparameters from `configs/experiments/v2_*_esp_fi.yaml` (not the frozen session-grouped artifact weights).
5. Prints **test macro-F1** on `test_amp`.

Treat the output as a **sanity check** against the authors’ packaging, not as a replacement for the thesis ladder.

---

## Related documents

- [`docs/thesis-benchmark-ladder.md`](thesis-benchmark-ladder.md) — seven-family results on session-grouped splits  
- [`docs/thesis-strengths-limitations.md`](thesis-strengths-limitations.md) — examiner-facing synthesis  
- [`reports/esp_fi_split_methodology.md`](../reports/esp_fi_split_methodology.md) — how R-View splits are built  
- [`configs/datasets/esp_fi_published_split.json`](../configs/datasets/esp_fi_published_split.json) — manifest for leakage checks  
