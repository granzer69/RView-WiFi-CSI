---
cursor:
  subagentId: "bc-b9f78fe2-50ec-5679-b3c1-486f10d209fe"
---

# Visual CSI Activity Simulator — Design

Design-only document for Ribhu's WiFi CSI HAR project. No simulator implementation, FastAPI production backend, WebSocket server, model training, ESP32 firmware, auth, or cloud services are in scope here.

**Evidence base (inspected 8 Oct 2026):** `/workspace` on `main` contains a V1 data foundation (Python): `src/datasets/esp_fi.py`, `src/ingestion/schema.py` (`CsiWindow`), `src/preprocessing/pipeline.py`, `src/csi/visualize.py`, configs under `configs/`, tests, and `reports/esp_fi_inspection.json` / `reports/esp_fi_split_methodology.md`. There is **no** `frontend/` tree yet. Locked roadmap remains software-first, ESP32 at V4 only.

**Primary simulated source:** ESP-Fi HAR — 2240 trials, each one session (`session_id` = stem `X-Y-Z-M`), matrix `CSIamp` shape `(950, 52)` amplitude only, phase and antenna axis absent, `sample_rate_hz` and per-matrix `timestamp` intentionally `null` on `CsiWindow` per schema policy.

---

## SIMULATOR ARCHITECTURE

### Purpose

Provide a **Visual CSI Activity Simulator** that behaves like a live WiFi sensing source **before V4 hardware**, using ESP-Fi recordings as the stand-in for an ESP32 CSI stream. The simulator educates stakeholders, unblocks dashboard UX, and validates the ingestion → preprocessing → inference **contract** without claiming real-time localization or hardware fidelity.

### Layered structure

```text
┌─────────────────────────────────────────────────────────────┐
│  Presentation (React dashboard — future implementation)      │
└───────────────────────────┬─────────────────────────────────┘
                            │ typed events (CSI frames, predictions, session state)
┌───────────────────────────▼─────────────────────────────────┐
│  Transport (pluggable)                                         │
│  • V1/V2: LocalReplayTransport / MockStreamClient (in-browser │
│    or dev-server SSE; no production WebSocket)                 │
│  • V3: WebSocket client → FastAPI `/stream` (hook only here)  │
└───────────────────────────┬─────────────────────────────────┘
┌───────────────────────────▼─────────────────────────────────┐
│  Simulator core (Python or TS worker — TBD at implement)       │
│  • SessionController (play/pause/stop/restart, speed)          │
│  • ReplayClock (nominal Hz × speed multiplier)                 │
│  • FrameEmitter (time index → CsiFrame / CsiWindow slice)    │
│  • Optional: InferenceBridge (V2+) → PredictionEvent           │
└───────────────────────────┬─────────────────────────────────┘
┌───────────────────────────▼─────────────────────────────────┐
│  Abstract data source                                          │
│  interface CsiStreamSource {                                   │
│    id, capabilities, open(session), readNext(), close()       │
│  }                                                             │
│  ├─ DatasetReplaySource  (V1–V3 simulator; ESP-Fi now)        │
│  └─ ESP32CSIStreamSource (V4; same interface, not built)      │
└─────────────────────────────────────────────────────────────┘
```

### Abstract `CsiStreamSource`

| Implementation | When | Reads from |
| --- | --- | --- |
| `DatasetReplaySource` | V1 simulator through V3 replay service | `TrialRecord` + `load_window()` (`src/datasets/esp_fi.py`) |
| `ESP32CSIStreamSource` | V4 | Serial/UDP adapter → `CsiWindow` (design placeholder only) |

Both must emit the **same** canonical `CsiWindow` (or a streaming subset with identical metadata keys) so preprocessing and inference never branch on source type.

### Replay engine (behavioral spec)

| Control | Behavior |
| --- | --- |
| **Play** | Advance replay clock; emit frames on tick |
| **Pause** | Stop clock; retain index and buffers |
| **Stop** | Pause and mark session ended (no auto-reset) |
| **Restart** | Reset time index to 0, clear bounded UI buffers, optionally re-`open()` same trial |
| **Speed** | `0.25×`, `0.5×`, `1×`, `2×`, `4×` multipliers on **replay clock**, not on ML inference wall time |

**Session selection:** User picks `session_id` (or filters: `scenario_id`, `participant_id`, `normalized_label`, `trial_id`). Default catalog is full ESP-Fi grid; published `train_amp` / `test_amp` folders are **leakage-check presets only**, not the primary simulator catalog (per `reports/esp_fi_split_methodology.md`).

**Frame granularity (design choice for implementation):**

1. **Index mode (recommended default):** One emitted frame = one row of `(950, 52)` per tick. Nominal rate defaults to **~95 Hz** (observed raw CSV packet rates ~93–99 Hz per scenario in `esp_fi_inspection.json`), with UI label “nominal replay rate — matrix index, not verified capture clock.”
2. **Trial mode:** Emit entire trial as one window at 1× duration (~10 s nominal) for static inspection; not for “live” demo.
3. **Preprocessed windows (V2+):** When `PreprocessConfig.window_length` is set, emitter yields segments from `preprocessing.pipeline.process()` — still one session per trial.

**Bounded memory:** Ring buffers for last *N* frames (CSI) and *M* predictions (e.g. N=500, M=100). Never retain full 2240-trial corpus in UI memory.

### Preprocessing alignment with inference

- Simulator passes frames through the **same** `PreprocessConfig` loaded with the active model artifact (V2+), or `configs/preprocessing/default.json` (no clip, no z-score, single full-trial segment) during V1 UI-only replay.
- **Rule:** If the dashboard shows “model input,” the config hash/version must match the loaded model bundle; mismatch → blocking banner, not silent relabel.
- Amplitude-only: no phase plots unless a future source provides phase.

### Source indicator

Global status chip (always visible):

- **Dataset Replay** — `source: "dataset_replay"`, dataset `esp-fi-har`, version from metadata.
- **ESP32 Live** (future) — `source: "esp32_stream"` (V4).

---

## FRONTEND ARCHITECTURE

### Stack (target)

- **React 18+**, **TypeScript**, **Vite** dev server, **Tailwind CSS**, **shadcn/ui** for primitives.
- Charting: **uPlot** or **visx** for performant heatmaps/time series (avoid shipping matplotlib to the browser).
- State: React context + reducers, or Zustand; **no** preprocessing or model weights in the frontend.

### Module layout (future repo paths)

```text
frontend/
├── src/
│   ├── pages/
│   │   ├── OverviewPage.tsx
│   │   └── LiveSensingPage.tsx      # primary simulator view
│   ├── components/
│   │   ├── layout/                  # shell, nav, integrity legend
│   │   ├── session/                 # picker, transport controls
│   │   ├── activity/                # ground truth + prediction cards
│   │   ├── spatial/                 # floor plan + SIMULATED badge
│   │   └── csi/                     # heatmap, subcarrier, waveform, timeline
│   ├── hooks/
│   │   ├── useReplaySession.ts
│   │   └── usePredictionStream.ts
│   ├── services/
│   │   ├── replayClient.ts          # LocalReplayTransport | WebSocketClient
│   │   └── api.ts                   # V3 REST (health, models, sessions)
│   └── types/
│       ├── csi.ts
│       ├── prediction.ts
│       └── session.ts
```

### Dashboard layout (Live Sensing)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Header: project title │ Source: [Dataset Replay ▼] │ model status │
├──────────────┬───────────────────────────────────────────────────┤
│ Session      │  Activity panel                                     │
│ picker       │  • Ground truth (dataset label, verification flag)  │
│ filters      │  • Model prediction (when V2+ connected)          │
│              │  • Confidence / latency                             │
├──────────────┼───────────────────────────────────────────────────┤
│ Transport    │  Spatial view (SIMULATED POSITION — see below)      │
│ ⏮ restart    │  static room outline per scenario_id                │
│ ⏯ play/pause │  animated icon — not metrology                      │
│ ⏹ stop       ├───────────────────────────────────────────────────┤
│ Speed 0.25–4x│  CSI views (tabs or grid)                           │
│              │  [Heatmap] [Subcarrier] [Waveform] [Timeline]       │
├──────────────┴───────────────────────────────────────────────────┤
│ Integrity legend: REAL DATA | SIMULATED POSITION | MODEL PREDICTION │
└──────────────────────────────────────────────────────────────────┘
```

### Research integrity (UI chrome)

Three visual tiers, never mixed without labels:

| Tier | Color/badge | Meaning |
| --- | --- | --- |
| **REAL DATA** | solid border | ESP-Fi amplitude, session metadata, ground-truth activity from filename map |
| **SIMULATED POSITION** | dashed amber + “Simulated” | Floor-plan coordinates; not in dataset |
| **MODEL PREDICTION** | blue | Output of inference engine; may disagree with ground truth |

Show `label_verified_by_folder: false` for all archive `mat/` paths today (`folder_verified_labels: 0` in inspection report) — tooltip explains scenario-3 folder map vs README.

### Responsive behavior

- Desktop: two-column layout above.
- Mobile: stack session controls → activity → spatial (collapsed) → CSI tabs.

### Empty / loading / error

- No trial selected: prompt to choose session.
- Loading trial: skeleton on heatmap.
- Missing local data path: “ESP-Fi archive not mounted” with link to `data/README.md` (dev message only).

---

## DATA REPLAY FLOW

### End-to-end sequence

```text
User selects session_id "3-2-4-1"
    → DatasetReplaySource.open(record)
    → load_window(record) → CsiWindow (950×52) + metadata
    → SessionController.reset(); ReplayClock at t=0
User presses Play @ 1×
    → each tick: emit CsiStreamFrame {
         time_index, wall_timestamp, amplitude_row[52],
         metadata (session_id, scenario_name, normalized_label, …)
       }
    → UI updates heatmap column / waveform / timeline cursor
Optional (V2+): InferenceBridge accumulates buffer → process() → predict()
    → emit PredictionEvent on same transport
User presses Pause / Stop / Restart / changes speed
    → controller state machine (no duplicate timers)
```

### Catalog discovery

Reuse `discover_trials(root)` from Python for backend; for pure frontend V1 mock, ship a **session manifest JSON** generated by `scripts/inspect_esp_fi.py` (or a thin export script) — list of `{ session_id, scenario_id, scenario_name, participant_id, activity_code, normalized_label, label_verified_by_folder }` without embedding amplitude blobs.

### Timing model

| Field | ESP-Fi reality | Simulator handling |
| --- | --- | --- |
| `CsiWindow.sample_rate_hz` | `null` (unknown for MAT) | Config `nominal_replay_hz` default 95; user-visible disclaimer |
| Raw CSV timestamps | ~10 s span, ~950–990 packets | Optional “CSV timing mode” later; not required for V1 UI |
| Matrix rows | 950 | Replay duration at 1× ≈ `950 / nominal_replay_hz` seconds |

### Streaming to UI (V1/V2 transport options)

1. **In-process (dev):** Vite proxy to a minimal **replay stub** (`POST /dev/replay/session`, `GET /dev/replay/events` SSE) — not the V3 FastAPI app.
2. **Static mock:** Pre-recorded JSONL per session for UI tests without Python.
3. **V3:** Replace stub with FastAPI session service + `WS /stream` (see integration plan).

Events on the wire (conceptual):

```typescript
type ReplayEvent =
  | { type: "session_started"; session_id: string; source: "dataset_replay" }
  | { type: "csi_frame"; time_index: number; subcarriers: number[]; meta: SessionMeta }
  | { type: "prediction"; payload: Prediction }
  | { type: "session_ended"; reason: "stop" | "complete" }
  | { type: "error"; message: string };
```

### Activity display (ground truth)

Show only labels the dataset supports — seven activities via `normalized_label`:

`running`, `walking`, `jumping`, `squatting`, `arm_wave`, `turning`, `falling`.

Display `dataset_label` and `activity_code` in an advanced panel. Never show README’s alternate code→label mapping as ground truth without a “README map (disputed)” warning.

**Do not** show published-split membership as “evaluation result”; optional badge “in published train_amp (leakage check only).”

---

## SPATIAL VISUALIZATION PLAN

### What exists in ESP-Fi (real)

| Field | Source | Spatial? |
| --- | --- | --- |
| `scenario_id` 1–4 | filename | Environment **category** only (corridor, office, boardroom, laboratory) |
| `scenario_name` | `SCENARIO_NAMES` in code | Human-readable room **type**, not dimensions |
| `participant_id` | filename | Subject id, not position |
| `session_id`, `trial_id` | filename | Trial identity |
| CSI amplitude | `.mat` | Signal, not coordinates |
| Raw CSV | sibling `csv/` | `timestamp`, `len`, CSI payload — **no x/y** |

**Conclusion:** ESP-Fi provides **no legitimate x/y coordinates or track geometry**. Any floor-plan position is **SIMULATED POSITION**.

### What to visualize as REAL DATA

- Time–subcarrier heatmap (`save_heatmap` parity).
- Mean and selected subcarrier waveforms (`save_amplitude_plot` parity).
- Timeline: ground-truth activity band for full trial; cursor at `time_index`.
- Environment badge: `scenario_name` + `scenario_id`.
- Participant/trial ids as metadata chips (not PII beyond participant index).

### SIMULATED POSITION (clearly labeled)

Purpose: UX placeholder for future tracking (post–V4 / optional V5), **not** research output.

| Element | Simulation rule |
| --- | --- |
| Room outline | One static SVG per `scenario_id` (generic rectangles; sizes arbitrary, labeled “illustrative”) |
| Actor icon | Start at room center; motion = canned keyframes per `normalized_label` (e.g. walk = back-and-forth path, fall = drop animation) |
| Coordinates | Normalized `x`, `y` in `[0, 1]`; `spatial.simulated: true` always for replay |
| Progress | Tie to `time_index / 949`, not to CSI-derived localization |

**Copy requirements:** Banner on spatial panel: “Simulated position for demonstration only. ESP-Fi does not include location labels.”

### What not to show

- Absolute meters, GPS, or “accuracy” metrics for position.
- Claims that model predicts location (until a future explicit task and labels exist).
- README “meeting room” vs archive “boardroom” as conflicting facts — show primary `scenario_name` with footnote on README alias.

---

## DATA CONTRACT

### `CsiWindow` (canonical — already in repo)

Streaming slices should carry the same `metadata` keys as `load_window()` (`dataset_id`, `session_id`, `scenario_id`, `normalized_label`, `label_verified_by_folder`, etc.). Partial windows must include `time_index_start` / `time_index_end` when not full trial.

### `SessionMeta` (simulator extension)

```json
{
  "session_id": "3-2-4-1",
  "environment_id": "boardroom",
  "scenario_id": 3,
  "participant_id": 2,
  "trial_id": 1,
  "activity_code": 4,
  "normalized_label": "squatting",
  "dataset_label": "squat",
  "label_verified_by_folder": false,
  "data_tier": "real"
}
```

`environment_id` = string slug of `scenario_name` (stable for API); not a second dataset.

### `Prediction` (model-agnostic frontend contract)

Frontend consumes this shape from inference or mock; fields optional until V2:

```json
{
  "activity": "walking",
  "confidence": 0.94,
  "timestamp": "2026-10-08T17:57:00.000Z",
  "session_id": "1-1-2-1",
  "environment_id": "corridor",
  "latency_ms": 12.4,
  "source": "model",
  "presence": true,
  "probabilities": {
    "walking": 0.94,
    "running": 0.02,
    "standing": 0.01
  },
  "model_version": "cnn_lstm_v1",
  "spatial": {
    "x": 0.42,
    "y": 0.67,
    "simulated": true
  }
}
```

| Field | Notes |
| --- | --- |
| `activity` | Normalized label vocabulary (seven classes) |
| `source` | `"model"` \| `"dataset_replay"` (if echoing ground truth for debug) |
| `spatial.simulated` | **Required** when `spatial` present; `true` for all ESP-Fi replay and until V4+ real tracking exists |
| `probabilities` | May omit classes; UI shows top-k |

Ground-truth echo (debug only, not a prediction):

```json
{
  "activity": "walking",
  "confidence": 1.0,
  "timestamp": "2026-10-08T17:57:00.000Z",
  "session_id": "1-1-2-1",
  "environment_id": "corridor",
  "latency_ms": 0,
  "source": "dataset_replay",
  "spatial": { "x": 0.5, "y": 0.5, "simulated": true }
}
```

### TypeScript mirrors

`frontend/src/types/prediction.ts` and `csi.ts` should match the JSON above; backend Pydantic models in V3 should generate OpenAPI from the same schema.

---

## V1/V2/V3 INTEGRATION PLAN

### Roadmap alignment vs early simulator

| Version | Official roadmap | This simulator |
| --- | --- | --- |
| **V1** | Data foundation, visualization | **Design now**; optional thin replay stub for CSI plots only; no WebSocket requirement |
| **V2** | ML engine + artifact | Connect `InferenceBridge`; show MODEL PREDICTION tier; ground truth for comparison |
| **V3** | FastAPI + WebSocket replay | Production path: session API + stream; replace dev stub |

**Conflict resolution:** V3.2 “dataset replay” is the **production** transport. V1/V2 **mock/local replay** is explicitly allowed for frontend development (per project assignment) but must use separate `LocalReplayTransport` and must not be documented as the final architecture.

### V3 FastAPI hook points (implement later)

| Endpoint / channel | Responsibility |
| --- | --- |
| `GET /health` | Liveness |
| `GET /models` | Active model + preprocess config hash |
| `GET /datasets` | Manifest summary (session count, not raw blobs) |
| `POST /sessions` | `{ source: "dataset_replay", session_id, speed, preprocess_config_id? }` |
| `GET /sessions/{id}` | State: playing, index, speed |
| `POST /sessions/{id}/control` | `{ action: "play" \| "pause" \| "stop" \| "restart", speed? }` |
| `WS /stream` | Multiplex `csi_frame` + `prediction` events |
| `POST /predict` | One-shot on full window (evaluation/dashboard) |

Service boundaries (match `.cursor/04_SYSTEM_ARCHITECTURE.md`):

```text
api/routes/          → thin handlers
api/services/
  replay_service.py  → DatasetReplaySource + SessionController
  inference_service.py → load bundle, predict
api/websocket/       → fan-out bounded events
```

### V4 swap

`ReplayService` selects `CsiStreamSource` implementation via config:

`source_type=dataset_replay | esp32_stream`

ESP32 adapter outputs `CsiWindow`; dashboard changes source chip to **ESP32 Live**; spatial remains `simulated: true` until a labeled tracking task exists.

### V1 validation repo coupling

Implementation agents should use `git worktree` if `/workspace` is locked by validation work. This design references existing modules read-only:

- `src/datasets/esp_fi.py` — discovery and load
- `src/preprocessing/pipeline.py` — alignment
- `src/csi/visualize.py` — reference for plot semantics

---

## FILES TO CREATE

When implementation is approved (not part of this design task):

| Path | Purpose |
| --- | --- |
| `docs/csi-activity-simulator-design.md` | Copy or link this store doc into repo after approval |
| `frontend/` | Vite + React + TS + Tailwind scaffold |
| `frontend/src/types/prediction.ts` | Prediction contract |
| `frontend/src/types/csi.ts` | Frame + session types |
| `frontend/src/services/replayClient.ts` | Transport abstraction |
| `frontend/src/hooks/useReplaySession.ts` | Play/pause/speed state |
| `frontend/src/components/csi/*` | Heatmap, waveform, timeline |
| `frontend/src/components/spatial/SimulatedFloorPlan.tsx` | SVG + badges |
| `src/simulator/__init__.py` | Python package |
| `src/simulator/sources/base.py` | `CsiStreamSource` protocol |
| `src/simulator/sources/dataset_replay.py` | `DatasetReplaySource` |
| `src/simulator/sources/esp32_stream.py` | Stub for V4 |
| `src/simulator/session_controller.py` | Transport controls |
| `src/simulator/clock.py` | Speed multipliers |
| `scripts/export_session_manifest.py` | JSON catalog for frontend |
| `api/` (V3) | FastAPI routes/services/websocket as above |
| `tests/test_simulator_session.py` | State machine + bounds |
| `tests/test_replay_contract.py` | Event schema snapshots |

Optional: `configs/simulator/default.json` — `nominal_replay_hz`, buffer sizes.

---

## RISKS / LIMITATIONS

| Risk | Impact | Mitigation |
| --- | --- | --- |
| **No spatial ground truth in ESP-Fi** | Users confuse demo animation with localization | `spatial.simulated: true`; permanent banner; no meter claims |
| **Label map disputed with README** | Wrong activity shown if README used | Locked map in `esp_fi.py`; UI shows verification flag; all `mat/` trials unverified by folder in current archive |
| **Inferred labels for scenarios 1, 2, 4** | Ground truth may be wrong | Display “inferred from filename code”; never claim folder-verified |
| **MAT vs CSV timing mismatch** | Misleading “real-time” feel | Default index replay with nominal Hz disclaimer; do not equate 950 rows to CSV packet count |
| **`sample_rate_hz` null** | Cannot reconstruct true capture clock | Do not invent rate on `CsiWindow`; simulator uses explicit `nominal_replay_hz` config only |
| **V3 vs early mock replay** | Architecture drift | Name transports distinctly; delete stub paths when V3 ships |
| **Published train/test folders** | Accidental leakage narrative | Presets labeled “leakage check only”; not default evaluation split |
| **Amplitude-only** | Phase/subcarrier phase views empty | Hide phase UI; document absence |
| **Performance** | Heatmap at 95 Hz × 52 may stress browser | Throttle render (e.g. 15 FPS display); decimate for chart |
| **Model not ready in V1** | Empty prediction panel | Mock toggle for UI dev; clear “no model loaded” state |
| **Taxonomy vs broader HAR specs** | Seven classes only | No “standing”, “lying”, etc. unless dataset added |

### Spec conflicts noted

1. **Roadmap V3.2 vs V1/V2 simulator:** Resolved by dual transport — dev mock now, WebSocket later.
2. **Architecture doc inference JSON** lacks `session_id`, `environment_id`, `spatial` — frontend contract in this doc **extends** V3 example for dashboard needs; backend OpenAPI should converge in V3.
3. **“Spatial intelligence” in agent workflow** is aspirational (V5 optional); simulator spatial is **explicitly non-research**.

---

## Approval checklist

- [ ] Ribhu approves simulated spatial UX and integrity labeling
- [ ] Confirm nominal replay Hz default (95) vs index-only stepping
- [ ] Confirm V1 allows Python replay stub vs static JSONL-only frontend
- [ ] After approval, implementation agent copies this file into git `docs/` via worktree
