# Challenge 3 — the exact commands, step by step

Everything a participant types, in order. Prompts go to Claude; `/goal`,
`/loop`, `/usage` are slash commands; `$` lines run in a terminal.

## Step 1 — hand off the check

> The summary stat cards on the dashboard don't add up - Total says 18 but
> the three status cards below it sum to 16. Find out why and fix it.

*(verify by hand, count your turns)*

> Create a skill at `.claude/skills/verify-fleet-change/SKILL.md` that
> encodes how we verify FleetOS dashboard changes end-to-end: run
> `python3 checks/check_dashboard.py` and report the pass count, curl
> http://localhost:8001/vehicles and /ops/incidents and expect 200 + JSON,
> re-read changed files, and never report done on a successful edit alone.
> If any step fails, fix and rerun from the top.

> The Open Incidents card on the dashboard always shows 0, even though
> /ops/incidents has open incidents. Fix it so the card shows the live
> count of unresolved incidents, and verify with the verify-fleet-change
> skill before reporting done.

## Step 2 — hand off the stop condition

> Build the Ops Feed card the checks describe, so that
> `python3 checks/check_dashboard.py` passes 12/12.

*(run the check yourself — usually 9–11/12)*

```
/goal python3 checks/check_dashboard.py prints "12/12 PASSED" - stop after 6 turns
```

> continue

*(mid-run:)* `/goal`      *(after:)* `/goal clear`

## Step 3 — hand off the trigger

```
$ python3 depot_sim.py            # Terminal B
```

*(once, then again after two heartbeats — feel the human setInterval:)*

> curl http://localhost:8001/ops/incidents and find unresolved incidents
> whose INC-id is not yet in OPS_LOG.md. Append one line per new incident
> to OPS_LOG.md (id, vehicle, severity, category, description). Then
> rewrite ../dashboard/live/ops_status.json as {"open_count": <number of
> unresolved incidents>, "last_incident": "<one-line summary of the
> newest>", "updated_at": "<current ISO timestamp>"}. Verify with the
> verify-fleet-change skill. If nothing is new, say "no new incidents" and
> change nothing.

```
/loop 2m curl http://localhost:8001/ops/incidents and find unresolved incidents whose INC-id is not yet in OPS_LOG.md. Append one line per new incident to OPS_LOG.md (id, vehicle, severity, category, description). Then rewrite ../dashboard/live/ops_status.json with {"open_count", "last_incident", "updated_at"} as before. Verify with the verify-fleet-change skill. If nothing is new, say "no new incidents" and do nothing else.
```

*(the staged failure:)*

```
$ python3 depot_sim.py --duplicate      # spare terminal
$ python3 checks/db_query.py dupes      # CONTENT_DUP >= 1 (organic doubles count too)
```

> Add a rule to the verify-fleet-change skill: after updating OPS_LOG.md,
> run `python3 checks/db_query.py dupes`; if CONTENT_DUP is above 0, mark
> the later report in OPS_LOG.md as "duplicate of INC-<id>" and count the
> pair once in ops_status.json's open_count.

*(when done: tell Claude "stop the loop" — Esc only interrupts the firing in flight, the schedule survives)*

## Step 4 — hand off the prompt

```
$ python3 depot_sim.py --tickets --duration 12m     # Terminal B
```

> Read inbox/TICKET-0001.md and do exactly what its "Definition of done"
> says. Then move it to done/.

*(add `"defaultMode": "dontAsk"` to .claude/settings.json, restart claude)*

```
/goal a run is only done when inbox/ contains no ticket file older than 2 minutes and every processed ticket has a row or line in TRIAGE.md or OPS_LOG.md - stop after 4 turns per run
```

```
/loop 2m process the ticket queue: for every file in inbox/, do exactly what its "Definition of done" section says, verify with the verify-fleet-change skill, then file it with `mv inbox/<name> done/`. If inbox/ is empty, reply "queue empty" and do nothing else.
```

*(coffee. then: write your own ticket, drop it in inbox/, watch. Say
"stop the loop" + `/goal clear` to go off shift.)*

## Step 5 — off shift

```
/usage
```
