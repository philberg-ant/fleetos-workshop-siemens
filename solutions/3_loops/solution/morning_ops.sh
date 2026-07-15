#!/usr/bin/env bash
# The enterprise stand-in for /schedule: the same standing prompt, run
# headless on any machine that stays on (a build server, an ops box, your
# desktop). Pair it with cron for a real schedule. This is all a time-based
# loop is — Challenge 3's `claude -p` pattern plus a clock.
#
# Run it from a plain terminal inside 3_loops/starter/ (NOT inside Claude
# Code):   ../../solutions/3_loops/solution/morning_ops.sh [interval-seconds]
set -euo pipefail

INTERVAL="${1:-120}"

while true; do
  claude -p "process the ticket queue: for every file in inbox/, do exactly what its \"Definition of done\" section says, verify with the verify-fleet-change skill, then file it with \`mv inbox/<name> done/\`. If inbox/ is empty, reply \"queue empty\" and do nothing else." \
    --permission-mode acceptEdits \
    || echo "run failed (exit $?) — retrying next interval"
  echo "── next run in ${INTERVAL}s (Ctrl-C to go off shift) ──"
  sleep "$INTERVAL"
done
