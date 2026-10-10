# Cursor integrated browser (Cloud Agent)

## Environment

This project runs on a **Cursor Cloud Agent VM** (remote Linux container). Your **integrated browser** runs on **your machine**; it reaches the app through **port forwarding**, not by opening the VM’s desktop Chrome.

| Role | Where it runs | URL you use in Cursor |
| --- | --- | --- |
| Vite (UI) | VM `0.0.0.0:43123` | **`http://127.0.0.1:43123`** on **your** machine (forwarded) |
| FastAPI (API) | VM `0.0.0.0:45231` | Forward **45231** as well (WebSocket + `/api` proxy) |

The VM’s own `http://127.0.0.1:43123` is **not** your laptop’s localhost unless the port is forwarded (green in the Ports panel).

## Start the dev stack (no external browser)

From the repository root:

```bash
bash scripts/dev-stack.sh start
```

Or only the frontend (API must already be up):

```bash
cd frontend && BROWSER=none npm run dev
```

`BROWSER=none`, `server.open: false`, and no `--open` flag prevent Vite from launching a desktop browser on the VM.

Check health:

```bash
bash scripts/dev-stack.sh status
```

Stop duplicates before a clean restart:

```bash
bash scripts/dev-stack.sh stop
bash scripts/dev-stack.sh start
```

Logs: `/tmp/rview-vite.log`, `/tmp/rview-api.log`.

## Port forwarding (manual Cursor UI — required)

1. Open the **Agents** chat for this cloud run.
2. Click the **plug icon** (**Forwarded Ports** / **Ports**).
3. Turn **Auto-Forward Ports** **ON** (recommended).
4. Confirm **43123** (web) and **45231** (api) show a **green** active indicator.
5. On the **43123** row, click the **globe** → **Open in internal browser** (or equivalent “open in Cursor browser”).
6. Do **not** rely on Windows/macOS Chrome at `127.0.0.1:43123` unless that port is forwarded in Cursor.

If you see `ERR_EMPTY_RESPONSE` or `ERR_CONNECTION_ABORTED`: the tunnel often hit a **Vite restart**. Run `bash scripts/dev-stack.sh status`, then **close** the broken tab, click the **globe** on **43123** again, and hard-refresh.

If ports stay broken: **Developer: Reload Window**, reopen the agent, `bash scripts/dev-stack.sh stop && bash scripts/dev-stack.sh start`, then repeat step 5.

## Declared ports

`.cursor/environment.json` registers **43123** and **45231** for auto-forward on environment builds that use this repo.

## Verify

On the VM:

```bash
curl -s -o /dev/null -w "UI %{http_code}\n" http://127.0.0.1:43123/
curl -s http://127.0.0.1:45231/health
```

In Cursor’s internal browser: **Visual CSI Activity Simulator** loads, **Dataset Replay** source, session picker, and **Live replay** / **Evaluation** tabs work.
