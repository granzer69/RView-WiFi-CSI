# V3 platform build guide

V3 turns V2 artifacts into a **modular monolith** FastAPI service with HTTP inference, **WebSocket-first dataset replay**, model selection, and a React dashboard. **Final project scope is software-only** — see `docs/project-scope.md` (ESP-Fi + replay + ML + UI; no ESP32).

## Layout

| Path | Role |
|------|------|
| `src/api/main.py` | FastAPI app (`create_app`, `app`) |
| `src/api/inference.py` | Inference on amplitude windows (all V2 families) |
| `src/api/model_registry.py` | Discovery under `artifacts/v2_*` + active model |
| `src/api/replay_stream.py` | `WS /ws/stream` replay + predictions + timeline events |
| `src/api/replay_manifest.py` | `GET /replay/manifest` from ESP-Fi root |
| `src/simulator/sources/dataset_replay.py` | Shared replay engine (tests + API) |
| `frontend/` | Vite UI; proxies `/api` and `/ws` → API port |
| `scripts/export_evaluation_summary.py` | Builds evaluation JSON for the UI |

## HTTP routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness, active model, load errors |
| `GET` | `/models` | All `v2_logreg`, `v2_rf`, `v2_cnn1d`, `v2_gru` strategy folders |
| `PUT` | `/models/active` | Body `{ "model_id": "..." }` — reload inference |
| `GET` | `/replay/manifest` | Session catalog from `RVIEW_DATA_ROOT` |
| `POST` | `/predict` | Direct classify (fallback / tools) |
| `WS` | `/ws/stream` | **Preferred** replay + `csi_frame` + `prediction` events |

### `POST /predict`

- Body: `{ "amplitude": number[][] }` — time-major, max **950 × 52** (ESP-Fi).
- Optional: `session_id`, `environment_id`, `time_index`, `frame_count` (spatial progress).
- Response: `activity`, `confidence`, `presence` (derived), `source: "model"`, `spatial.simulated: true`, `model_version`, `probabilities`.

### `WS /ws/stream`

Client JSON messages:

- `{"type":"open_session","session_id":"<esp-fi-session>"}`
- `{"type":"control","action":"play|pause|stop|restart","speed":1}`
- `{"type":"select_model","model_id":"v2_rf_in_domain_..."}`
- `{"type":"ping"}`

Server events:

- `model_status` (on connect and after model change)
- `session_started`, `csi_frame`, `prediction`, `timeline`, `session_ended`, `error`

Prediction payloads use `source: "dataset_replay"` on the WebSocket path; HTTP `/predict` uses `source: "model"`.

Buffers are bounded by `RVIEW_WS_BUFFER_ROWS` (default 950).

## Configuration

| Variable | Default |
|----------|---------|
| `RVIEW_MODEL_DIR` | `artifacts/v2_rf/20261010T060000Z/in_domain` |
| `RVIEW_MODEL_ID` | optional; overrides default artifact via registry id |
| `RVIEW_DATA_ROOT` | `data/raw/esp-fi-har` |
| `RVIEW_CORS_ORIGINS` | `http://127.0.0.1:43123,http://localhost:43123` |
| `RVIEW_WS_BUFFER_ROWS` | `950` |

Frontend (Vite):

| Variable | Default |
|----------|---------|
| `VITE_API_URL` | `/api` (proxied to `127.0.0.1:45231`) |
| `VITE_USE_API_PREDICTIONS` | enabled unless `false` |
| `VITE_USE_WS_REPLAY` | enabled unless `false` |

## Run API + frontend (examiner demo)

```bash
# Terminal 1 — API (port 45231)
cd /workspace
pip install -e ".[dev,ml]"
python3 scripts/run_api.py

# Terminal 2 — evaluation JSON (optional but recommended)
python3 scripts/export_evaluation_summary.py

# Terminal 3 — simulator UI (port 43123)
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:43123** → Live replay. Open **/evaluation** for V2 metrics.

### Demo script (≈3 minutes)

1. Confirm **Source: Dataset Replay** and transport **WS /ws/stream** (requires ESP-Fi at `RVIEW_DATA_ROOT`).
2. Select session `1-1-2-1`, press **Play** — heatmap and model card update each frame.
3. Open **ACTIVITY** tab — compare ground truth vs model; note `spatial.simulated`.
4. Sidebar **Active model** — switch to `logreg` or `cnn1d` strategy; replay continues with new artifact.
5. **SYSTEM** tab — model status, WS timeline snippet.
6. **Evaluation** nav — confusion matrix / F1 tabs per split strategy.

### Replay without full trial export

When ESP-Fi is on the API machine, WebSocket replay loads trials server-side. For offline-only UI, export trials:

```bash
python3 scripts/export_replay_manifest.py --export-trials 1-1-2-1 1-1-1-1
# or all sessions (large):
python3 scripts/export_replay_manifest.py --all-trials
```

## Integrity labels

- **Source chip:** Dataset Replay (ESP-Fi CSI; not live hardware).
- **Ground truth:** `source: dataset_replay`, dataset labels (inferred where noted).
- **Model card:** trained artifact; spatial track **simulated**.
- **Presence:** derived from confidence / activity (not mmWave hardware).

## Tests

```bash
python3 -m pytest   # includes tests/test_api_v3.py
cd frontend && npm run build
```

## Completed V3 capabilities

- WebSocket-first dashboard with HTTP/local fallback
- Model picker (all V2 families + split strategies)
- Evaluation dashboard (V3.6) via `summary.json`
- Model status + session timeline events on WS
- Software-only scope documented (`docs/project-scope.md`)

## Out of scope

ESP32 live stream, CSI-Bench download, auth/k8s, microservices, V4/V5 hardware programs.
