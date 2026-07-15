#!/usr/bin/env bash
# Reset Challenge 5 working state — rewind the morning.
# Rebuilds fleet_ops.db in place so a running API keeps serving without a
# restart (it opens a fresh connection per request).
set -euo pipefail
cd "$(dirname "$0")"

rm -f OPS_LOG.md TRIAGE.md
rm -f inbox/TICKET-*.md done/TICKET-*.md
rm -rf ../dashboard/live __pycache__ checks/__pycache__
rm -rf .claude/skills/verify-fleet-change

cp .baseline/app.js .baseline/index.html .baseline/styles.css ../dashboard/
cp .baseline/vehicles.json ../dashboard/data/vehicles.json

python3 - <<'EOF'
import sqlite3
from pathlib import Path
data = Path("../fleetos_api/data").resolve()
db = data / "fleet_ops.db"
db.unlink(missing_ok=True)
conn = sqlite3.connect(db)
conn.executescript((data / "schema.sql").read_text(encoding="utf-8"))
conn.commit()
conn.close()
print("✓ fleet_ops.db rebuilt from schema.sql")
EOF

echo "✓ Reset complete. Restart depot_sim.py if it was running."

if grep -q '"defaultMode"' .claude/settings.json 2>/dev/null; then
  echo "⚠️  .claude/settings.json still sets defaultMode (added in Step 4) —"
  echo "   remove that line if you want to restart the morning interactively."
fi
