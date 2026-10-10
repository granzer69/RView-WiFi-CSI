# Cursor in-app browser (Preview / Forwarded Ports)

Desktop Chrome on the **agent VM** can reach `http://127.0.0.1:43123` directly. The **internal browser** in the Cursor Agents window runs on **your machine** and uses **port forwarding** from the cloud VM.

## If Preview shows `ERR_CONNECTION_ABORTED` or `ERR_EMPTY_RESPONSE`

1. Ensure dev servers are running on the agent (API **45231**, UI **43123**), bound to **0.0.0.0**:
   ```bash
   bash scripts/start-cursor-dev.sh
   ```
   Or two terminals: `python3 scripts/run_api.py` and `cd frontend && npm run dev`.

2. In the **Agents** panel, open the **plug icon** (Forwarded Ports).
3. Enable **Auto-Forward Ports** or manually forward **43123** (and **45231** if needed).
4. Choose **Open in internal browser** on port **43123** — do not paste `127.0.0.1:43123` into an external browser on Windows unless that port is forwarded.

5. If forwarding looks stale after an environment snapshot: **Developer: Reload Window**, reopen the project, ask the agent to restart `start-cursor-dev.sh`, then open the forwarded port again.

## Declared ports

`.cursor/environment.json` lists `43123` (web) and `45231` (api) so new agent boots can register them for forwarding. Changes apply on the **next** agent that uses that environment build.

## URLs on the VM (Desktop only)

| Service | URL |
| --- | --- |
| UI | http://127.0.0.1:43123 |
| API health | http://127.0.0.1:45231/health |
