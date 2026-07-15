---
id: TICKET-0001
type: triage
created: 2026-07-09
---

# Triage the newest incident

The ops desk logged a new driver report. Triage it.

## Definition of done

- [x] Look up the newest **unresolved** incident with `python3 checks/db_query.py open` (top row).
- [x] Check on `http://localhost:8001/vehicles` whether that vehicle is also `overdue` for service.
- [x] Append one row to `TRIAGE.md`: `| TICKET-0001 | INC-<id> <vehicle> <severity> | <recommended action> | <check result> |`
- [x] Move this ticket file to `done/`.
