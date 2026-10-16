# Viva demo script (~15 minutes, software-only)

**Audience:** examiners and supervisors  
**Hardware:** none — **dataset replay** only (bundled JSON trials and/or ESP-Fi-backed WebSocket replay)  
**Stack:** `bash scripts/dev-stack.sh start-preview` → UI **http://127.0.0.1:43123**, API **http://127.0.0.1:45231** (see [`SETUP.md`](SETUP.md))

---

## Before you start (2 min, off-camera or while sharing terminal)

1. From repo root: `bash scripts/dev-stack.sh status` — expect UI **200**, API **ok**, `model_loaded: true`.
2. Open the UI in the browser (forward ports **43123** and **45231** in Cursor Cloud).
3. Confirm the header shows **`DATASET REPLAY`** — this is not live Wi-Fi sensing.

**Sound bite:** *“Everything you will see is reproducible offline: frozen models in `artifacts/v2_*`, metrics exported to JSON, and CSI replay from the public ESP-Fi HAR corpus or bundled demo trials.”*

---

## Route map (this repository on `main`)

| Step | Narrative label | URL / navigation | What to show |
| --- | --- | --- | --- |
| 1 | **Live** | `/` → tab **Sensing** | Session picker, transport controls, CSI heatmap + waveform updating on **Play** |
| 2 | **Activity** | `/` → tab **Activity analysis** | Ground truth vs model prediction, timeline, class distribution |
| 3 | **Models** | `/` → left sidebar **Active model** / model picker | Switch families (e.g. RF → logreg → cnn1d); note split strategy in label |
| 4 | **Explorer** | `/` → tab **Diagnostics** (explorer-style integrity view on `main`) | Manifest source, transport mode (JSON vs WebSocket), connection chip |
| 5 | **Research** | `/research` | Generalization gaps, participant overview, personalization caveats |
| 6 | **Evaluation** (optional if time) | `/evaluation` | Per-split metrics grid, confusion matrices from `frontend/public/evaluation/summary.json` |

**V4 Sensing Studio routes** (when merged: dedicated pages): `/activity`, `/models`, `/explorer`, `/experiments`. The flow below is unchanged; only navigation moves from tabs/sidebar to top-level routes.

---

## Minute-by-minute script

### 0:00–2:30 — Live sensing (`/`)

1. Land on **Sensing** (default tab). Point out **DATASET REPLAY** and **Research workstation · ESP-Fi amplitude replay (no hardware)**.
2. Select session **`1-1-2-1`** (bundled demo trial; environment 1, user 1, scenario 2, trial 1).
3. Press **Play** — heatmap and subcarrier waveform advance; **Summary** bar shows ground truth vs prediction.
4. Mention **replay vs live:**
   - **Replay (this demo):** pre-recorded ESP-Fi amplitude windows; predictions from the API using frozen artifacts.
   - **Live (out of thesis scope):** would require ESP32 CSI capture and real-time RF conditions — not claimed here.
   - **WebSocket replay** (optional): with ESP-Fi at `data/raw/esp-fi-har/`, the API can stream trials; without it, **JSON trials** under `frontend/public/replay/trials/` still drive the UI.

### 2:30–5:00 — Activity (`/` → Activity analysis)

1. Open **Activity analysis** tab.
2. Walk through **current frame** labels vs **model** output and the **timeline** strip.
3. If predictions lag or disagree with ground truth on cross-user-like sessions, preview the limitation close: *in-domain metrics ≠ new users*.

### 5:00–7:30 — Models (sidebar on `/`)

1. Open the **model picker**; default is often **random forest · in_domain**.
2. Switch to **logistic regression** — note it is stronger on **cross-user** in the benchmark ladder.
3. Try **cnn1d** or **gru** — discuss as **fair baselines**, not heavily tuned SOTA.
4. Say explicitly: metrics in the UI are read from **`artifacts/.../metrics.json`**, not typed into the frontend.

### 7:30–9:30 — Explorer / diagnostics (`/` → Diagnostics)

1. Open **Diagnostics** tab.
2. Show **transport mode** (local JSON vs API/WebSocket) and manifest timing note.
3. Tie to validity: session-grouped splits, label inference for scenarios 1/2/4 — pointer to [`research-validity-audit.md`](research-validity-audit.md).

### 9:30–12:30 — Research Lab (`/research`)

1. Open **Research Lab** from the nav.
2. **Generalization** — RF leads in-domain; logreg relatively better on cross-user; discuss **gaps** (in-domain minus cross-user macro-F1).
3. **Participants** — who appears in which split (session-grouped assignment).
4. **Personalization** — exploratory in-domain calibration only; **not** leave-one-user-out (LOUO eval in progress separately).

### 12:30–14:30 — Evaluation (`/evaluation`) if time

1. Show the **split strategy** columns: `in_domain`, `cross_user`, `cross_environment`.
2. One confusion matrix for RF in-domain vs logreg cross-user — reinforces “no single winner on every axis.”

### 14:30–15:00 — Limitations close

Read or paraphrase from [`thesis-strengths-limitations.md`](thesis-strengths-limitations.md):

- Single public dataset (ESP-Fi) for headline numbers; label uncertainty outside scenario 3.
- Offline replay ≠ deployed Wi-Fi sensing.
- Deep models under default configs; contribution is **fair comparison + tooling**, not exhaustive HPO.
- Personalization UI ≠ unseen-user generalization; **LOUO** extension documented in project plan.

---

## Suggested sample trial

| Field | Value |
| --- | --- |
| Session ID | `1-1-2-1` |
| Why | Bundled in repo; plays without ESP-Fi on disk |
| Alternate | `1-1-1-1` for a second scenario in the same environment/user |
| Talking point | Scenario **3** has folder-verified labels; scenarios **1/2/4** use inferred labels (see ladder + audit) |

---

## Fallbacks

| Issue | What to do |
| --- | --- |
| Empty session list | Use bundled trials; or export manifest with ESP-Fi present (`scripts/export_replay_manifest.py`) |
| `model_loaded: false` | Check `RVIEW_MODEL_DIR` points at `artifacts/v2_rf/20261010T060000Z/in_domain` |
| Blank page in Cursor browser | `start-preview` + hard refresh; see [`cursor-in-app-browser.md`](cursor-in-app-browser.md) |
| WS replay errors | Set `VITE_USE_WS_REPLAY=false` or rely on JSON trials |

---

## Related docs

- [`thesis-contributions.md`](thesis-contributions.md) — contributions and results headline  
- [`thesis-benchmark-ladder.md`](thesis-benchmark-ladder.md) — full metrics table  
- [`smoke-test.md`](smoke-test.md) — reproducibility checklist before the viva  
- [`SETUP.md`](SETUP.md) — ports, env vars, install
