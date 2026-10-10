# V3 platform build guide

V3 turns the V2 trained artifacts into a **modular monolith** FastAPI service with HTTP inference, dataset replay over WebSocket, and a simulator UI that calls real model predictions while keeping **Dataset Replay** as the CSI source and **simulated** spatial positions.

## Layout

| Path | Role |
|------|------|
| `src/api/main.py` | FastAPI app (`create_app`, `app`) |
| `src/api/inference.py` | RF inference on amplitude windows |
| `src/api/model_registry.py` | Artifact discovery and default model load |
| `src/api/replay_stream.py` | `DatasetReplaySource` + `WS /ws/stream` |
| `src/simulator/sources/dataset_replay.py` | Shared replay engine (tests + API) |
| `frontend/` | Vite UI; proxies `/api` → API port |

## HTTP routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness + whether the default model loaded |
| `GET` | `/models` | RF artifacts under `artifacts/v2_rf/` |
| `POST` | `/predict` | Classify a bounded amplitude window |
| `WS` | `/ws/stream` | Server-side dataset replay + prediction events |

### `POST /predict`

- Body: `{ "amplitude": number[][] }` — time-major, max **950 × 52** (ESP-Fi).
- Optional: `session_id`, `environment_id`, `time_index`, `frame_count` (for spatial progress).
- Response: `activity`, `confidence`, `timestamp`, `session_id`, `source: "model"`, `spatial.simulated: true`, `model_version`, `probabilities`.

### `WS /ws/stream`

Client JSON messages:

- `{"type":"open_session","session_id":"<esp-fi-session>"}`
- `{"type":"control","action":"play|pause|stop|restart","speed":1}`

Server events:

- `session_started`, `csi_frame`, `prediction`, `session_ended`, `error`

Prediction payloads use `source: "dataset_replay"` on the WebSocket path (replay contract); HTTP `/predict` uses `source: "model"`.

## Configuration

| Variable | Default |
|----------|---------|
| `RVIEW_MODEL_DIR` | `artifacts/v2_rf/20261010T060000Z/in_domain` |
| `RVIEW_DATA_ROOT` | `data/raw/esp-fi-har` |
| `RVIEW_CORS_ORIGINS` | `http://127.0.0.1:43123,http://localhost:43123` |

Frontend (Vite):

| Variable | Default |
|----------|---------|
| `VITE_API_URL` | `/api` (proxied to `127.0.0.1:45231`) |
| `VITE_USE_API_PREDICTIONS` | enabled unless `false` |

## Run API + frontend together

```bash
# Terminal 1 — API (port 45231)
cd /workspace
pip install -e ".[dev]"
python3 scripts/run_api.py

# Terminal 2 — simulator UI (port 43123)
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:43123`. CSI still loads from exported trial JSON; each frame calls `POST /predict` with the amplitude prefix so the dashboard shows **V2 RF** outputs.

## Integrity labels (unchanged from V1)

- **Source chip:** Dataset Replay (real ESP-Fi CSI in the browser).
- **Ground truth:** `source: dataset_replay`, real labels.
- **Model card:** `source: model`, trained RF artifact; spatial track remains **simulated**.

## Tests

```bash
python3 -m pytest   # includes tests/test_api_v3.py (HTTP + WebSocket smoke)
cd frontend && npm run build
```

## Out of scope (this slice)

ESP32 live stream, CSI-Bench download, auth/k8s, microservices, CNN/GRU serving tuning.
