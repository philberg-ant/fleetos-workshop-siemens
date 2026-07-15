#!/usr/bin/env python3
"""Read-only access to fleet_ops.db for Challenge 5.

The simulator and the API own the database — everyone else (you, Claude,
loops) reads it through this helper. It opens the file read-only, so it can
never corrupt the world.

This file is FROZEN: fix your workflow, never the tooling.

Usage:
    python3 checks/db_query.py open           # open incidents, newest first
    python3 checks/db_query.py incident 14    # one incident in full
    python3 checks/db_query.py dupes          # duplicate-report detector
    python3 checks/db_query.py sql "SELECT count(*) FROM fuel_log"
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

DB_DEFAULT = Path(__file__).resolve().parents[2] / "fleetos_api" / "data" / "fleet_ops.db"


def connect(db: Path) -> sqlite3.Connection:
    if not db.exists():
        sys.exit(f"error: {db} not found — start the API first, it builds the database")
    conn = sqlite3.connect("file:" + quote(str(db)) + "?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def cmd_open(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT id, vehicle_id, severity, category, reported_at, description"
        " FROM incidents WHERE resolved = 0 ORDER BY id DESC"
    ).fetchall()
    for r in rows:
        desc = r["description"]
        if len(desc) > 60:
            desc = desc[:57] + "..."
        print(f"INC-{r['id']:<4} {r['vehicle_id']}  {r['severity']:<6} "
              f"{r['category']:<13} {r['reported_at']}  {desc}")
    print(f"OPEN={len(rows)}")
    return 0


def cmd_incident(conn: sqlite3.Connection, incident_id: int) -> int:
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    if row is None:
        print(f"no incident with id {incident_id}")
        return 1
    for key in row.keys():
        print(f"{key}: {row[key]}")
    return 0


def cmd_dupes(conn: sqlite3.Connection) -> int:
    """Open incidents that share vehicle AND category are probably the same
    problem reported twice. A triage loop should merge them, not double-log."""
    rows = conn.execute(
        "SELECT a.id AS first_id, b.id AS second_id, a.vehicle_id, a.category"
        " FROM incidents a JOIN incidents b"
        "   ON a.vehicle_id = b.vehicle_id AND a.category = b.category AND a.id < b.id"
        " WHERE a.resolved = 0 AND b.resolved = 0"
        " ORDER BY b.id"
    ).fetchall()
    for r in rows:
        print(f"INC-{r['second_id']} looks like a re-report of INC-{r['first_id']}"
              f" ({r['vehicle_id']}, {r['category']})")
    print(f"CONTENT_DUP={len(rows)}")
    return 0


def cmd_sql(conn: sqlite3.Connection, query: str) -> int:
    if not query.lstrip().lower().startswith("select"):
        sys.exit("error: only SELECT statements are allowed — the database is read-only")
    rows = conn.execute(query).fetchall()
    if rows:
        print(" | ".join(rows[0].keys()))
        for r in rows:
            print(" | ".join(str(r[k]) for k in r.keys()))
    print(f"ROWS={len(rows)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=DB_DEFAULT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("open")
    p_incident = sub.add_parser("incident")
    p_incident.add_argument("id", type=int)
    sub.add_parser("dupes")
    p_sql = sub.add_parser("sql")
    p_sql.add_argument("query")
    args = parser.parse_args()

    conn = connect(args.db)
    try:
        if args.command == "open":
            return cmd_open(conn)
        if args.command == "incident":
            return cmd_incident(conn, args.id)
        if args.command == "dupes":
            return cmd_dupes(conn)
        return cmd_sql(conn, args.query)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
