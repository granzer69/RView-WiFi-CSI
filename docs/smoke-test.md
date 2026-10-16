# Smoke test — defense / reproducibility

Run this checklist on a clean clone before a viva or before merging defense-readiness changes. **No hardware** required for the minimum path; full replay catalog needs ESP-Fi on disk.

**Reference:** ports and env vars in [`SETUP.md`](SETUP.md).

---

## 1. Prerequisites

| Check | Command / expectation |
| --- | --- |
| Python **3.11+** | `python3 --version` |
| Node **20+** | `node --version` |
| Repo root | `pwd` ends in `RView-WiFi-CSI` (or your clone name) |

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev,ml]"
cd frontend && npm ci && cd ..
```

---

## 2. Automated gates (CI parity)

From repository root:

```bash
python3 -m pytest -q
```

| Result | Meaning |
| --- | --- |
| **~47 passed**, ESP-Fi tests **skipped** | OK without dataset |
| ESP-Fi tests **passed** | OK with full archive at `data/raw/esp-fi-har/` |

```bash
cd frontend && npm run build && cd ..
```

Expect `frontend/dist/` produced with no TypeScript/Vite errors.

---

## 3. ESP-Fi HAR (optional but recommended)

**Path:** `data/raw/esp-fi-har/` (gitignored)

1. Download and extract [ESP-Fi-HAR](https://github.com/AutoSmartGroup/ESP-Fi-HAR) per `data/README.md`.
2. Layout must include `EnvironmentNo.1(corridor)/`, … with `mat/` and `csv/` subtrees.
3. Verify:

```bash
python3 scripts/inspect_esp_fi.py
# expect 2240 trials; writes reports/esp_fi_inspection.json
```

4. Refresh replay manifest (optional):

```bash
PYTHONPATH=src python3 scripts/export_replay_manifest.py
```

**Symlink:** If the archive lives elsewhere, symlink into place:

```bash
ln -s /path/to/extracted/ESP-Fi-root data/raw/esp-fi-har
```

Set `RVIEW_DATA_ROOT` if using a non-default path (API reads this for WebSocket replay).

---

## 4. Start the stack

From repo root:

```bash
bash scripts/dev-stack.sh stop   # if a previous run exists
bash scripts/dev-stack.sh start-preview
bash scripts/dev-stack.sh status
```

| Service | URL | Acceptance |
| --- | --- | --- |
| UI | http://127.0.0.1:**43123** | HTTP 200 |
| API health | http://127.0.0.1:**45231**/health | JSON `status: ok`, `model_loaded: true` |

**Cursor Cloud:** forward ports **43123** and **45231**; open globe on 43123.

Manual alternative:

```bash
# Terminal 1
python3 scripts/run_api.py    # binds 45231

# Terminal 2
cd frontend && BROWSER=none npm run dev   # 43123
```

---

## 5. UI acceptance checklist

| # | Step | Pass criteria |
| --- | --- | --- |
| 1 | Open http://127.0.0.1:43123/ | Page loads; **DATASET REPLAY** badge visible |
| 2 | Session **1-1-2-1** → **Play** | CSI heatmap animates; time index advances |
| 3 | Tab **Activity analysis** | Ground truth + model prediction shown |
| 4 | Change **model** (sidebar) | Active model label updates; predictions may change |
| 5 | Tab **Diagnostics** | Transport mode + manifest info visible |
| 6 | Nav → **Evaluation** (`/evaluation`) | Model cards load from `summary.json` |
| 7 | Nav → **Research Lab** (`/research`) | Generalization section loads; integrity note visible |
| 8 | API | `curl -s http://127.0.0.1:45231/health` shows `model_loaded: true` |

**With ESP-Fi present (extra):**

| # | Step | Pass criteria |
| --- | --- | --- |
| 9 | Session picker | More than bundled demo sessions listed |
| 10 | WebSocket replay | Diagnostics shows non-local transport when `VITE_USE_WS_REPLAY` enabled |

---

## 6. Artifacts integrity

Do **not** modify frozen benchmark trees:

- `artifacts/v2_logreg/20261010T045500Z/`
- `artifacts/v2_rf/20261010T060000Z/`
- `artifacts/v2_cnn1d/20261010T070000Z/`
- `artifacts/v2_gru/20261010T080000Z/`

Evaluation UI numbers should match `metrics.json` in those directories (see [`thesis-benchmark-ladder.md`](thesis-benchmark-ladder.md)).

---

## 7. Stop

```bash
bash scripts/dev-stack.sh stop
```

Logs: `/tmp/rview-vite.log`, `/tmp/rview-api.log`.

---

## 8. Failure quick reference

| Symptom | Fix |
| --- | --- |
| `pytest` import errors | `pip install -e ".[dev,ml]"` from root |
| `model_loaded: false` | Confirm `artifacts/v2_rf/.../in_domain` exists |
| Empty manifest | Run export script or use bundled trials `1-1-1-1`, `1-1-2-1` |
| Frontend build fails | `cd frontend && npm ci` then `npm run build` |
| Port in use | `bash scripts/dev-stack.sh stop` |

---

## Related

- [`viva-demo-script.md`](viva-demo-script.md) — examiner walkthrough  
- [`SETUP.md`](SETUP.md) — full install and troubleshooting  
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) — GitHub Actions parity
