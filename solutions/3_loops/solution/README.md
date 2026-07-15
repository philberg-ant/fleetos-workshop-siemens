# Challenge 3 — reference solution

This is the state a participant reaches at end of shift:

- `dashboard/` — all 12 checks passing: the Retired card (Step 1 bug A),
  the live Open Incidents count (Step 1 bug B), and the Ops Feed card
  (Step 2). Point the referee at it to confirm:
  `python3 ../../../3_loops/starter/checks/check_dashboard.py --dashboard dashboard`
- `.claude/skills/verify-fleet-change/SKILL.md` — the verification skill
  in its final form, **including the duplicate-guard rule added in
  Step 3**.
- `.claude/settings.json` — the Step 4 end state (`defaultMode: "dontAsk"`
  on top of the pre-seeded allowlist + hook).
- `PROMPTS.md` — every prompt, `/goal` and `/loop` invocation, in order.
- `morning_ops.sh` — the headless stand-in for `/schedule` (Step 6 /
  Bedrock path).
- `OPS_LOG.md`, `TRIAGE.md`, `done/TICKET-0001.md`,
  `dashboard/live/ops_status.json` — sample artefacts from one run.
  **Yours will differ** — the simulator is seeded, but your loop timing
  isn't.
