# Setup and run guide

Everything you need to clone **R-View WiFi CSI** and run the V3 demo locally or in **Cursor Cloud Agents**. For architecture and results, see [`what-we-built.md`](what-we-built.md).

**Repository:** https://github.com/granzer69/RView-WiFi-CSI

---

## 1. Requirements

| Tool | Version | Used for |
| --- | --- | --- |
| **Git** | any recent | Clone |
| **Python** | **3.11+** (3.12 tested) | API, training, data scripts |
| **Node.js** | **20+** (22 tested) | Frontend (`npm`) |
| **npm** | 10+ | Comes with Node |

**Disk (approximate):**

| Item | Size | In git? |
| --- | ---: | --- |
| Repository + `artifacts/` (trained models) | ~50 MB | Yes |
| ESP-Fi HAR extracted | ~several GB | **No** — you download separately |
| `frontend/node_modules/` | ~200 MB | No — `npm ci` |
| Python venv | ~1–2 GB with PyTorch | No — `pip install` |

**OS:** Linux, macOS, or Windows (WSL recommended for shell scripts).

---

## 2. Clone

```bash
git clone https://github.com/granzer69/RView-WiFi-CSI.git
cd RView-WiFi-CSI
```

The repo includes:

- Source code (`src/`, `frontend/`, `scripts/`, `configs/`, `tests/`)
- Reports and docs (`reports/`, `docs/`)
- **Pre-trained V2 models** under `artifacts/v2_*` (logreg, RF, CNN, GRU)
- **Demo replay JSON** for two sessions: `frontend/public/replay/trials/1-1-1-1.json`, `1-1-2-1.json`
- **Evaluation summary** for the UI: `frontend/public/evaluation/summary.json`
- **CSI Explorer** (`/explorer`) and **Experiment Workbench** (`/experiments`) — see [`csi-explorer-user-guide.md`](csi-explorer-user-guide.md) and [`experiment-workbench-guide.md`](experiment-workbench-guide.md)

---

## 3. Python environment

From the **repository root**:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev,ml]"
```

| Extra | Purpose |
| --- | --- |
| `dev` | pytest, httpx, websockets (API tests) |
| `ml` | PyTorch (CNN/GRU training only; inference for deep models in API) |

Verify:

```bash
python3 -m pytest -q
# expect: 47 passed
```

---

## 4. Frontend dependencies

```bash
cd frontend
npm ci
cd ..
```

Use **`npm ci`** (not `npm install`) so versions match `package-lock.json`.

---

## 5. ESP-Fi HAR dataset (full live replay)

### When you need it

| Feature | Without ESP-Fi on disk | With ESP-Fi at `data/raw/esp-fi-har/` |
| --- | --- | --- |
| UI loads, demo trials | Yes (bundled JSON) | Yes |
| `GET /replay/manifest` (full catalog) | Empty / limited | Full 2240 sessions |
| WebSocket replay from API | No (use JSON fallback) | Yes |
| Training scripts | No | Yes |
| `inspect_esp_fi.py` | No | Yes |

### Acquire data

1. Open the official dataset: [AutoSmartGroup/ESP-Fi-HAR](https://github.com/AutoSmartGroup/ESP-Fi-HAR) (follow their README for download links — often Google Drive or similar).
2. Extract so the **root** of the archive matches:

```text
data/raw/esp-fi-har/
  EnvironmentNo.1(corridor)/
    mat/   … *.mat
    csv/   … *.csv
  EnvironmentNo.2（Office）/
  EnvironmentNo.3（boardrooms）/
  EnvironmentNo.4（kitchen）/   # name may match published tree
```

3. Confirm layout (optional but recommended):

```bash
python3 scripts/inspect_esp_fi.py
# writes reports/esp_fi_inspection.json, data/metadata/esp-fi-har.json
```

**Integrity:** Expected archive SHA-256 and label policy are in [`data/README.md`](../data/README.md).

### Refresh frontend manifest (after ESP-Fi is present)

```bash
# Default: export manifest + demo trials 1-1-1-1 and 1-1-2-1
PYTHONPATH=src python3 scripts/export_replay_manifest.py

# Or export all sessions (large JSON under frontend/public/replay/trials/)
PYTHONPATH=src python3 scripts/export_replay_manifest.py --all-trials
```

`PYTHONPATH=src` is required for these scripts unless you installed the package with `pip install -e .` (then `python3 scripts/...` alone is enough).

---

## 6. Start the application

All commands from **repository root**.

### Option A — Recommended for Cursor internal browser

Production UI bundle (stable through port forwarding); API still live.

```bash
bash scripts/dev-stack.sh start-preview
bash scripts/dev-stack.sh status
```

### Option B — Development (file watch, HMR disabled for forwarding)

```bash
bash scripts/dev-stack.sh start
```

### Option C — Manual terminals

```bash
# Terminal 1 — API (port 45231)
python3 scripts/run_api.py

# Terminal 2 — UI (port 43123)
cd frontend && BROWSER=none npm run dev
```

### Stop

```bash
bash scripts/dev-stack.sh stop
```

### URLs

| Service | On the machine where processes run | Notes |
| --- | --- | --- |
| UI | http://127.0.0.1:43123 | Live replay + Evaluation |
| API health | http://127.0.0.1:45231/health | `model_loaded`, active artifact |
| Evaluation page | http://127.0.0.1:43123/evaluation | Static JSON + charts |

Frontend proxies **`/api`** and **`/ws`** to the API (see `frontend/vite.config.ts`).

---

## 7. Cursor Cloud Agents (port forwarding)

Your **integrated browser** runs on your laptop; the app runs on the **agent VM**.

1. Start stack on the agent: `bash scripts/dev-stack.sh start-preview`
2. **Forwarded Ports** (plug icon) → enable **43123** and **45231** (green).
3. Click **globe** on **43123** → internal browser.
4. Hard refresh if blank after a restart.

Details: [`cursor-in-app-browser.md`](cursor-in-app-browser.md).

---

## 8. Environment variables

### API (`scripts/run_api.py`)

| Variable | Default | Description |
| --- | --- | --- |
| `RVIEW_MODEL_DIR` | `artifacts/v2_rf/20261010T060000Z/in_domain` | Active model directory |
| `RVIEW_MODEL_ID` | (optional) | Override via registry id |
| `RVIEW_DATA_ROOT` | `data/raw/esp-fi-har` | ESP-Fi root for manifest + WS replay |
| `RVIEW_CORS_ORIGINS` | `http://127.0.0.1:43123,http://localhost:43123` | CORS for browser |
| `RVIEW_WS_BUFFER_ROWS` | `950` | Max CSI rows buffered per WS session |

### Frontend (Vite)

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_URL` | `/api` | HTTP API base (proxied) |
| `VITE_USE_API_PREDICTIONS` | enabled | Set `false` to stub predictions |
| `VITE_USE_WS_REPLAY` | enabled | Set `false` for JSON-only replay |

### Dev stack

| Variable | Set by | Description |
| --- | --- | --- |
| `BROWSER=none` | `dev-stack.sh` | Prevents opening external browser |
| `RVIEW_CURSOR_PREVIEW=1` | `dev-stack.sh` | Disables Vite HMR (Cursor forwarding) |

---

## 9. Demo checklist (examiner, ~3 minutes)

1. `bash scripts/dev-stack.sh status` → UI **200**, API **ok**, `model_loaded: true`.
2. Open UI → **Dataset Replay** source visible.
3. Select session **1-1-2-1**, press **Play** → CSI heatmap updates.
4. **ACTIVITY** tab → ground truth vs model (RF default).
5. Change **Active model** (e.g. logreg, cnn1d).
6. **Evaluation** → metrics per split strategy.

Extended script: [`v3-platform-build-guide.md`](v3-platform-build-guide.md).

---

## 10. Optional: retrain models

Requires ESP-Fi at `data/raw/esp-fi-har/`.

```bash
python3 scripts/train_logreg.py
python3 scripts/train_rf.py
python3 scripts/train_cnn1d.py
python3 scripts/train_gru.py
python3 scripts/export_evaluation_summary.py
```

Outputs: `artifacts/v2_*/<run_id>/`, `reports/v2_*_results.md`, updated `frontend/public/evaluation/summary.json`.

Guide: [`v2-engine-build-guide.md`](v2-engine-build-guide.md).

---

## 11. Production frontend build (no dev server)

```bash
cd frontend
npm run build
npm run preview   # serves dist/ on 0.0.0.0:43123
```

For API + static UI in production, serve `frontend/dist` behind a reverse proxy and run `python3 scripts/run_api.py` separately (not fully automated in this repo).

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Blank white page in Cursor browser | Vite dev + HMR through tunnel | `bash scripts/dev-stack.sh stop` then `start-preview`; hard refresh |
| `ERR_EMPTY_RESPONSE` on 43123 | Stale port forward after API/Vite restart | Remove/re-add port **43123**, globe again |
| `model_loaded: false` | Missing artifact path | Confirm `artifacts/v2_rf/...` exists; set `RVIEW_MODEL_DIR` |
| No sessions in picker | No ESP-Fi + no export | Use bundled trials or run `export_replay_manifest.py` |
| WS replay fails | ESP-Fi not on API host | Use JSON trials or set `RVIEW_DATA_ROOT` |
| `pytest` import errors | Package not installed | `pip install -e ".[dev,ml]"` from repo root |
| Port in use | Old process | `bash scripts/dev-stack.sh stop` |

Logs (dev-stack): `/tmp/rview-vite.log`, `/tmp/rview-api.log`.

---

## 13. What is intentionally not in git

| Path | Reason |
| --- | --- |
| `data/raw/esp-fi-har/` | Large; CC BY 4.0 — download yourself |
| `data/interim/`, `data/processed/` | Generated |
| `frontend/node_modules/`, `frontend/dist/` | Install / build locally |
| `.venv/`, `.env` | Local environment |

---

## 14. Document index

| Doc | Contents |
| --- | --- |
| [`SETUP.md`](SETUP.md) | This file |
| [`what-we-built.md`](what-we-built.md) | Project narrative V1–V3 |
| [`project-scope.md`](project-scope.md) | In/out of scope |
| [`v3-platform-build-guide.md`](v3-platform-build-guide.md) | API & WebSocket reference |
| [`v2-engine-build-guide.md`](v2-engine-build-guide.md) | Training & splits |
| [`cursor-in-app-browser.md`](cursor-in-app-browser.md) | Cursor forwarding |
| [`data/README.md`](../data/README.md) | Dataset licenses & hashes |
