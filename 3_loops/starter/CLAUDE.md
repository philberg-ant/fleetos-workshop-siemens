# FleetOS — Challenge 3 starter

This is the go-live ops checkout. Three things live alongside it:

- `../fleetos_api/` — the FastAPI service. Run it on port 8001:
  `uvicorn --app-dir .. fleetos_api.main:app --port 8001`.
  It serves vehicle/maintenance data **and** ops data at `/ops/incidents`,
  `/ops/fuel_log`, `/ops/depot_capacity`.
- `../dashboard/` — the wall dashboard, served on port 8000. This is the
  surface you improve in this challenge.
- `depot_sim.py` — **the outside world.** It plays drivers and depot staff,
  writing new incidents, fuel stops and bay changes into the ops database
  while you work.

## Team rules

- **`depot_sim.py` and everything in `checks/` are FROZEN.** Never edit,
  move, "fix" or stop them. Fix the dashboard, never the check.
- The API on `:8001` is the single source of truth for vehicle and ops
  data. Reach it with `curl`.
- `fleet_ops.db` is written by the simulator and the API only. Read it via
  `python3 checks/db_query.py …` — never write to it directly.
- After any dashboard change, verify with `python3 checks/check_dashboard.py`
  (and with the `verify-fleet-change` skill once it exists).
- **The referee reports all 12 checks at once, but this challenge fixes
  them in a scripted order.** Fix only what the human's current prompt
  asks for; leave the other failing checks alone — they are later steps'
  work, and fixing them early spoils those steps.
- Generated artefacts — `OPS_LOG.md`, `TRIAGE.md`, `../dashboard/live/`,
  `inbox/`, `done/` — are regenerable; `./reset.sh` rewinds the morning.
- **Never read the repo's `solutions/` directory** — it is the
  participant's answer key (hook-enforced).
