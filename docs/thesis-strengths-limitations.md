# Thesis strengths and limitations (examiner-facing)

Concise synthesis for viva discussion. Full evidence: [`docs/research-validity-audit.md`](research-validity-audit.md), [`docs/thesis-benchmark-ladder.md`](thesis-benchmark-ladder.md), [`docs/esp-fi-official-split-comparison.md`](esp-fi-official-split-comparison.md).

---

## Strengths

1. **Leakage-aware evaluation** — Three session-grouped strategies (`in_domain`, `cross_user`, `cross_environment`) with **locked assignment SHA-256** hashes verified in training and `metrics.json`. Published `train_amp` / `test_amp` are documented as a **separate** leakage check, not the headline split ([`esp-fi-official-split-comparison.md`](esp-fi-official-split-comparison.md)).

2. **Reproducible artifact ladder** — Seven model families (logreg, RF, MLP, GBDT, 1D CNN, GRU, TCN) with frozen run IDs under `artifacts/v2_*/`. UI and exports read `metrics.json`; numbers are not hand-entered in the frontend (audit **PASS WITH LIMITATIONS**).

3. **Honest data and integrity UX** — Amplitude-only CSI; scenarios 1/2/4 labels **inferred** from the scenario-3 folder map; Research Lab surfaces the label caveat and personalization interpretation limits.

4. **Software contribution** — End-to-end pipeline: ingestion → training → evaluation dashboard → WebSocket replay demo without claiming live hardware deployment.

5. **Generalization framing** — Cross-user macro-F1 and **gaps** (in-domain minus shift split) are reported per family, supporting a nuanced “no single winner on every axis” narrative.

---

## Limitations

1. **Single public dataset in training** — ESP-Fi only for reported metrics; CSI-Bench / Embedded not in the thesis ladder (license / acquisition).

2. **Label uncertainty** — README vs folder activity codes disagree; non–scenario-3 labels are not independently verified.

3. **Deep models under-tuned** — CNN, GRU, and TCN use **default-config baselines** (fixed epochs / architecture from YAML), not a hyperparameter search. They are fairly compared under the same splits but should not be read as “best possible” deep learning.

4. **Personalization is not unseen-user** — In-domain A/B compares a global model that **already saw** each participant’s train sessions to a calibrator on those sessions. It does **not** demonstrate leave-one-user-out or cold-start users (audit F-01/F-02).

5. **Offline vs deployment** — No live Wi-Fi sensing, room dynamics, or device heterogeneity in the measured results.

6. **OSS / paper alignment** — Metrics follow R-View’s session-grouped protocol and preprocessing defaults, which differ from the authors’ scenario-3 participant holdout and typical z-score pipeline; use `compare_official_esp_fi_pack.py` only when local `train_amp` / `test_amp` folders exist.

---

## Suggested viva sound bites

- *“Cross-user is the deployment-critical axis; RF wins in-domain but logreg and GBDT are stronger on held-out participants under our splits.”*
- *“Deep models are deliberately under-tuned baselines on the same leakage-safe assignment — the contribution is fair comparison and tooling, not SOTA tuning.”*
- *“Personalization numbers are exploratory in-domain calibration, not evidence that the global model never saw that user’s training data.”*
