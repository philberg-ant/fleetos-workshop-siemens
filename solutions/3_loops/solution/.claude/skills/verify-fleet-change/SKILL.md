---
name: verify-fleet-change
description: Verify any FleetOS dashboard or ops change end-to-end before declaring it done. Use after every change to ../dashboard/ or to OPS_LOG.md / TRIAGE.md.
---

# Verifying FleetOS changes

Never report a change as complete based on a successful edit alone. Verify
it the way the ops team would:

1. Run `python3 checks/check_dashboard.py` and report the pass count
   ("N/12 PASSED") in your final message.
2. `curl -s http://localhost:8001/vehicles` and
   `curl -s http://localhost:8001/ops/incidents` — both must return
   HTTP 200 and valid JSON.
3. Re-read every file you changed and confirm the edit is what you
   intended.
4. **Duplicate guard** (added in Step 3): after updating `OPS_LOG.md`,
   run `python3 checks/db_query.py dupes`. If `CONTENT_DUP` is above 0,
   mark the later report in `OPS_LOG.md` as "duplicate of INC-<id>" and
   count the duplicated pair once in `ops_status.json`'s `open_count`.

If any step fails, fix the issue and rerun from step 1 — do not hand back
partially verified work.
