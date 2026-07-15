# Challenge 3 — Facilitator guide

The README is fully self-serve: a solo reader can run the whole morning
without a facilitator. This file is the *room overlay* — pacing, checkpoints,
pre-flight, and recovery — for delivering it to 10–25 people at once.

## Pre-flight (run this the week before, on the participants' setup)

The loop primitives are CLI-version and configuration sensitive. Do a full
dry run on a machine configured **the same way participants' machines will
be** (same auth backend — Anthropic API, Bedrock, or Vertex — same managed
settings, same network):

- [ ] `claude --version` — note it; `/goal` and `/loop` must both appear in
      the `/` menu. Require the same or newer version in the room.
- [ ] Folder-trust dialog: start `claude` in a fresh `starter/` checkout and
      confirm `/goal` works after accepting trust.
- [ ] Run **Step 2 end-to-end**: does the evaluator visibly bounce an early
      stop? Does bare `/goal` mid-run print turns + tokens? Adjust the
      README wording you present if behavior differs on your build.
- [ ] Run **Step 4 end-to-end unattended**: flip `defaultMode: "dontAsk"`,
      start the ticket loop, and *watch the transcript for silent
      auto-denials*. If Claude's composed commands fall outside the
      allowlist, widen `starter/.claude/settings.json` before the workshop —
      a denied command during the coffee break fails invisibly.
- [ ] Managed settings: if the org deploys `managed-settings.json`, confirm
      it permits `dontAsk`, project hooks, and project `settings.json` at
      all. If not, plan Step 4 as a facilitator demo from your machine.
- [ ] Rate limits: N participants × a `/goal` run × loop firings is a
      thundering herd. Confirm the org/account quota supports ~N concurrent
      Sonnet sessions (on Bedrock: TPM/RPM service quotas per region —
      check cross-region inference is enabled). Plan to stagger loop starts
      by table, and pre-decide "`/model haiku` for the loop steps" as your
      fallback call.
- [ ] Network: `uv pip install` must work through the venue network/proxy.
      Send the Step 0 commands as pre-work email; bring a wheelhouse
      (`pip download -d wheels/ -r requirements.txt`, install with
      `--no-index --find-links wheels/`) for casualties.
- [ ] Laptop OS: everything here is cross-platform (the hook is Python, the
      DB helper replaces the sqlite3 CLI), but on Windows rehearse the venv
      activation and `python` vs `python3` spelling and say it out loud in
      Step 0.

## Suggested schedule (~90 min room slot)

| When | What | Room checkpoint (don't proceed without it) |
| --- | --- | --- |
| 0:00 | Frame: the four handoffs table on a slide | — |
| 0:05 | Step 0 setup | Every pair: *Live API* badge + Swagger + Claude open. Budget 15 min honestly; pre-work email compresses it. |
| 0:20 | Step 1 — the check | Ask: *"who spent zero verification turns on the second bug?"* Tally turns-before vs turns-after on a whiteboard — it's the module's scoreboard. Expect TWO valid bug-A fixes in the room: adding a Retired card *or* excluding retired from Total — the referee accepts both; 30 seconds on "which would the ops team want?" is a nice bonus beat. |
| 0:35 | Step 2 — the stop condition | Ask: *"who saw the evaluator bounce Claude? how many times?"* Have one pair read their bare-`/goal` token readout aloud. |
| 0:50 | Step 3 — the trigger | Heartbeat check FIRST (a silent simulator ruins the step). During loop waits, run the interval-sizing discussion and `/usage`. Fire the `--duplicate` beat together, on your call. |
| 1:10 | Step 4 — the prompt | Stagger loop starts by table (front row first, 60 s apart). Then the whole room stands up for coffee — physically. Return, audit, write-your-own-ticket. |
| 1:25 | Step 5 — off shift | The summary table + three scenarios; go around: *"which piece of your real job do you hand off first?"* End with the room ceremonially telling Claude "stop the loop" + `/goal clear` (Esc only interrupts one firing — the schedule survives). |

**Trim to 60 min:** cut Step 3's duplicate beat and Step 4's
write-your-own-ticket (keep the coffee break — it *is* the pedagogy).
**Stretch to 2 h:** Step 6 Extend, especially the poisoned ticket and the
headless `morning_ops.sh` run.

## Mixed-audience pairing

Pair a **driver** (keyboard, Terminal C) with an **ops manager** (browser,
Terminal B, TRIAGE.md). The ops manager owns the *wording*: the skill's
checklist prose, the `/goal` sentence, the ticket they author in Step 4 —
all plain language, and precision-of-wording is the skill being taught.
Steps 1–2 are the floor (everyone finishes); Steps 3–4 reward pairs. Solo
non-devs may copy `solutions/3_loops/solution/dashboard/` after Step 2 —
the README already authorizes it implicitly via solutions/; say it out loud
so nobody stalls.

## Talking points at the two waits

- **Step 3, while the loop fires:** "The simulator ticks every 20 seconds.
  Your loop fires every 2 minutes. Who chose well? What does a 10-second
  loop cost at your org's token prices? What does a 30-minute loop cost in
  stale dashboards?" Then: `/usage`.
- **Step 4, before the coffee break:** walk `settings.json` on the
  projector. The point to land: *autonomy was safe because the fence came
  first* — allowlist + deny + hook. `dontAsk` auto-DENIES, it doesn't
  auto-approve.
- **`/schedule` (talk track, no demo needed):** "Same handoff as `/loop`,
  but the trigger lives in the cloud, so it survives your laptop. On
  Bedrock there's no claude.ai backend — your version of this is the
  pattern participants formalise later in Challenge 4: headless `claude -p` on a
  cron, on a box that stays on. `morning_ops.sh` in the solutions folder
  is exactly that."

## Recovery moves

| Symptom | Move |
| --- | --- |
| Pair's dashboard shows *Static data* | API not running or wrong dir — rerun the Step 0 uvicorn line **from `starter/`**. |
| Simulator silent | It waits for the DB and says so; if wedged, Ctrl-C and `python3 depot_sim.py --once` to prove one tick, then restart plain. |
| Anything wedged mid-morning | `./reset.sh` rewinds everything (DB rebuilt in place — API keeps running), restart the simulator. |
| `/goal` missing | Trust dialog not accepted, or old build — the README's 📝 fallback (stop condition in the prompt) keeps the pair moving. |
| Step 2 one-shots 12/12 | Use the README's 💡 reframe: `/goal` buys *who verified*, not capability. |
| Loop firing finds nothing | Simulator died or interval too short — check the heartbeat, restate the interval-sizing lesson with their case as the example. |
| Rate-limit stalls during Step 4 | Your pre-decided call: `/model haiku` for loops, and stagger the remaining tables. |
| "Claude refuses to open solutions/" | Working as designed — every starter ships a hook that keeps Claude out of the answer key (repo root `.claude/hooks/guard_solutions.py`). Participants who want to peek open the files themselves. |
