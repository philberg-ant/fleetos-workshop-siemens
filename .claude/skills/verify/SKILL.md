---
name: verify
description: Maintainer recipe for verifying changes to the FleetOS workshop stack end-to-end (API, dashboards, Challenge 3 simulator/checks). Not a participant exercise.
---

# Verifying FleetOS workshop changes

The stack has no test suite by design — verify by driving the real surfaces.

## Build & launch (Challenge 3/4/5 share the API shape)

```bash
cd <module>/starter
python3 -m uvicorn --app-dir .. fleetos_api.main:app --port 8001   # builds fleet_ops.db from schema.sql on first start
cd ../dashboard && python3 -m http.server 8000                     # serve any dashboard; solution copies work on another port
```

fastapi/uvicorn are importable from the system Homebrew python3 on this
machine — no venv needed for verification.

## Flows worth driving after a change

- `curl :8001/vehicles` and `:8001/ops/incidents` — statuses, re-dated
  seeds (Challenge 3 schema uses `date('now', '-N days')`), CORS header.
- Challenge 3 referee: `python3 checks/check_dashboard.py` must print
  **3/12** on the starter dashboard (C1, C2, C5 pass; C3/C4/C6 are the
  planted bugs, C7–C12 the unbuilt Ops Feed) and **12/12** with
  `--dashboard ../../solutions/3_loops/solution/dashboard`.
- Simulator: `python3 depot_sim.py --once`, `--duplicate` (then
  `python3 checks/db_query.py dupes` → `CONTENT_DUP=1`), and
  `--tickets --interval 1 --duration 4s` (TICKET-0001 lands on tick 1).
- Hook: `printf '%s' '{"tool_input":{"file_path":"depot_sim.py"}}' | python3 .claude/hooks/guard_sim.py`
  → block JSON; a `.bak` or renamed file must pass silently.
- `./reset.sh` while uvicorn is running — API must keep serving (12 seed
  incidents) without a restart, dashboard files restored from `.baseline/`
  **including data/vehicles.json**.
- Browser: starter dashboard must show Total 18 vs cards summing 16 and
  Open Incidents 0 (the planted bugs); solution must show Retired 2, live
  incident count, and an Ops Feed that self-updates within 15 s of
  rewriting `live/ops_status.json`.

## Gotchas

- Claude Code's sandbox blocks binding localhost ports AND curling
  localhost — run servers and any command that hits `:8001` with the
  sandbox disabled.
- The `/goal`+`/loop` participant flows can't be driven headlessly here —
  they're covered by the facilitator pre-flight in `3_loops/FACILITATOR.md`.
