# Project scope (approved)

**Status:** Approved scope change — **software-only, no hardware** (October 2026).

## In scope (final delivery)

| Layer | What ships |
| --- | --- |
| Data | ESP-Fi HAR adapter, session-grouped splits, canonical `CsiWindow`, integrity metadata |
| ML (V2) | Logistic regression, random forest, 1D CNN, GRU artifacts under `artifacts/v2_*` |
| Platform (V3) | FastAPI monolith: `GET /health`, `GET /models`, `PUT /models/active`, `POST /predict`, `GET /replay/manifest`, `WS /ws/stream` |
| Replay | Dataset replay from `data/raw/esp-fi-har` (API) and/or exported trial JSON (browser fallback) |
| UI | Live CSI simulator, model picker, evaluation dashboard, integrity labels |

ESP-Fi stands in for **live Wi-Fi sensing**: real published CSI matrices and labels, replayed in software without ESP32 firmware or serial capture.

## Explicitly out of scope (not planned unless reopened)

- **V4** ESP32 / live CSI hardware, firmware, UART bridges
- **V5** advanced tracking, multi-room robustness programs
- CSI-Bench automated download without credential approval
- Embedded WiFi Sensing HAR in experiment runners
- Auth, Kubernetes, microservices decomposition

## Demo acceptance (V3)

1. Start API + frontend (see `docs/v3-platform-build-guide.md`).
2. Open live replay, pick a session, press play.
3. Observe CSI heatmap, ground truth, and **live model predictions** (WebSocket path when ESP-Fi is on the API host).
4. Switch models via the sidebar picker (logreg / RF / CNN / GRU strategies).
5. Open **Evaluation** for offline metrics from `frontend/public/evaluation/summary.json`.

No physical hardware is required for this acceptance path.
