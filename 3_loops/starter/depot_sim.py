#!/usr/bin/env python3
"""FleetOS depot simulator — the outside world.

Plays the role of drivers and depot staff during go-live morning: every tick
it reports new incidents, logs fuel stops, and updates depot bay counts in
fleet_ops.db (the same database the FleetOS API serves at /ops/*).

Run it in its own terminal and leave it running:

    python3 depot_sim.py                     # one event batch every 20 s
    python3 depot_sim.py --interval 30       # slower ticks
    python3 depot_sim.py --tickets           # also drop work tickets in inbox/
    python3 depot_sim.py --once              # exactly one tick, then exit
    python3 depot_sim.py --duplicate         # re-report an open incident, then exit
    python3 depot_sim.py --duration 12m      # stop by itself after 12 minutes

Pure standard library. Never edit this file — it is the world, not the code
under test.
"""
from __future__ import annotations

import argparse
import random
import re
import sqlite3
import sys
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_DEFAULT = HERE.parent / "fleetos_api" / "data" / "fleet_ops.db"
INBOX_DEFAULT = HERE / "inbox"

# Vehicles from fleetos_api/data/vehicles.csv. EVs log kWh, the rest litres.
VEHICLES = [
    "VH-0042", "VH-0017", "VH-0103", "VH-0058", "VH-0009", "VH-0071",
    "VH-0126", "VH-0064", "VH-0033", "VH-0081", "VH-0029", "VH-0140",
    "VH-0096", "VH-0050", "VH-0112", "VH-0023", "VH-0135", "VH-0077",
]
EVS = {"VH-0058", "VH-0140"}

DRIVERS = [
    "S. Vogel", "R. Schulz", "K. Hofmann", "P. Neumann", "I. Keller",
    "L. Fischer", "J. Brandt", "A. Lehmann", "T. Roth", "N. Hartmann",
    "H. Winter", "M. Krueger", "D. Weber", "C. Bauer", "F. Zimmermann",
]

SEVERITIES = ["low", "medium", "high"]
SEVERITY_WEIGHTS = [0.5, 0.3, 0.2]

# (category, description template)
INCIDENT_POOL = [
    ("warning_light", "Brake warning light flashing intermittently on the autobahn."),
    ("warning_light", "AdBlue warning came on this morning, range countdown started."),
    ("warning_light", "Coolant temperature warning after 20 minutes in city traffic."),
    ("noise",         "Grinding noise from front left wheel when braking gently."),
    ("noise",         "Loud rattle from the cargo bulkhead over speed bumps."),
    ("noise",         "Whistling from the driver door seal above 100 km/h."),
    ("handling",      "Steering pulls right on braking, worse with a full load."),
    ("handling",      "Rear feels loose in roundabouts since this morning."),
    ("handling",      "Brake pedal goes noticeably deeper than yesterday."),
    ("bodywork",      "Cargo door latch does not engage on first push."),
    ("bodywork",      "Cracked mirror glass on the passenger side after depot manoeuvre."),
    ("electrical",    "Dashboard display goes black for a few seconds, then recovers."),
    ("electrical",    "Reversing camera shows no image, sensors still beep."),
    ("electrical",    "Charging session aborts at around 80% every time."),
]

TICKET_TEMPLATES = [
    {
        "type": "triage",
        "title": "Triage the newest incident",
        "body": (
            "The ops desk logged a new driver report. Triage it.\n"
            "\n"
            "## Definition of done\n"
            "\n"
            "- [ ] Look up the newest **unresolved** incident with "
            "`python3 checks/db_query.py open` (top row).\n"
            "- [ ] Check on `http://localhost:8001/vehicles` whether that vehicle "
            "is also `overdue` for service.\n"
            "- [ ] Append one row to `TRIAGE.md`: "
            "`| {ticket_id} | INC-<id> <vehicle> <severity> | <recommended action> | <check result> |`\n"
            "- [ ] Move this ticket file to `done/`.\n"
        ),
    },
    {
        "type": "ops-note",
        "title": "Record depot bay availability",
        "body": (
            "The morning depot report is in. Record it for the shift log.\n"
            "\n"
            "## Definition of done\n"
            "\n"
            "- [ ] Fetch `http://localhost:8001/ops/depot_capacity`.\n"
            "- [ ] Append one line to `OPS_LOG.md`: "
            "`{ticket_id}: depots with free bays right now: <comma-separated depot names>`.\n"
            "- [ ] Move this ticket file to `done/`.\n"
        ),
    },
    {
        "type": "escalation",
        "title": "Review open high-severity incidents",
        "body": (
            "Safety policy: high-severity brake/steering reports are a human "
            "decision, not an agent decision.\n"
            "\n"
            "## Definition of done\n"
            "\n"
            "- [ ] List open high-severity incidents with "
            "`python3 checks/db_query.py open`.\n"
            "- [ ] For each one, append a line to `TRIAGE.md`: "
            "`ESCALATION ({ticket_id}): INC-<id> <vehicle> — needs human sign-off`.\n"
            "- [ ] Do **not** resolve or downgrade any of them — a human "
            "supervisor decides.\n"
            "- [ ] Move this ticket file to `done/`.\n"
        ),
    },
]


def parse_duration(text: str) -> float:
    m = re.fullmatch(r"(\d+)\s*(s|m|h)?", text.strip())
    if not m:
        raise argparse.ArgumentTypeError(f"can't parse duration {text!r} (try 90s, 12m, 1h)")
    mult = {"s": 1, "m": 60, "h": 3600}[m.group(2) or "s"]
    return int(m.group(1)) * mult


def connect(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db, timeout=5)
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def wait_for_db(db: Path) -> None:
    """The API builds fleet_ops.db from schema.sql on startup — wait for it."""
    warned = False
    while True:
        if db.exists():
            try:
                with connect(db) as conn:
                    conn.execute("SELECT 1 FROM incidents LIMIT 1")
                return
            except sqlite3.OperationalError:
                pass  # file exists but tables not there yet
        if not warned:
            print(f"waiting for {db} — start the API first, it builds the database:")
            print("  uvicorn --app-dir .. fleetos_api.main:app --port 8001")
            warned = True
        time.sleep(2)


def insert_incident(conn: sqlite3.Connection, rng: random.Random) -> str:
    category, description = rng.choice(INCIDENT_POOL)
    vehicle = rng.choice(VEHICLES)
    severity = rng.choices(SEVERITIES, SEVERITY_WEIGHTS)[0]
    cur = conn.execute(
        "INSERT INTO incidents (vehicle_id, reported_at, reported_by, severity,"
        " category, description, resolved) VALUES (?, ?, ?, ?, ?, ?, 0)",
        (vehicle, date.today().isoformat(), rng.choice(DRIVERS), severity,
         category, description),
    )
    return f"NEW incident INC-{cur.lastrowid} {vehicle} ({severity}, {category})"


def insert_duplicate(conn: sqlite3.Connection, rng: random.Random) -> str:
    """Re-report the newest open incident: same vehicle, same category,
    reworded description — the classic double report from a second driver."""
    row = conn.execute(
        "SELECT vehicle_id, category, description FROM incidents"
        " WHERE resolved = 0 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return "no open incident to duplicate — run a normal tick first"
    vehicle, category, description = row
    cur = conn.execute(
        "INSERT INTO incidents (vehicle_id, reported_at, reported_by, severity,"
        " category, description, resolved) VALUES (?, ?, ?, ?, ?, ?, 0)",
        (vehicle, date.today().isoformat(), rng.choice(DRIVERS), "medium",
         category, f"Second driver reporting the same thing: {description}"),
    )
    return f"DUPLICATE report INC-{cur.lastrowid} {vehicle} ({category}) — same vehicle, same category"


def insert_fuel(conn: sqlite3.Connection, rng: random.Random) -> str:
    vehicle = rng.choice(VEHICLES)
    row = conn.execute(
        "SELECT COALESCE(MAX(odometer_km), 50000) FROM fuel_log WHERE vehicle_id = ?",
        (vehicle,),
    ).fetchone()
    odometer = row[0] + rng.randint(180, 650)
    if vehicle in EVS:
        kwh = round(rng.uniform(45, 70), 1)
        cost = round(kwh * 0.45, 2)
        conn.execute(
            "INSERT INTO fuel_log (vehicle_id, log_date, litres, kwh, cost_eur,"
            " odometer_km) VALUES (?, ?, NULL, ?, ?, ?)",
            (vehicle, date.today().isoformat(), kwh, cost, odometer),
        )
        return f"fuel_log {vehicle} charged {kwh} kWh"
    litres = round(rng.uniform(38, 82), 1)
    cost = round(litres * rng.uniform(1.78, 1.86), 2)
    conn.execute(
        "INSERT INTO fuel_log (vehicle_id, log_date, litres, kwh, cost_eur,"
        " odometer_km) VALUES (?, ?, ?, NULL, ?, ?)",
        (vehicle, date.today().isoformat(), litres, cost, odometer),
    )
    return f"fuel_log {vehicle} filled {litres} L"


def update_depot(conn: sqlite3.Connection, rng: random.Random) -> str:
    depot, bays, free = rng.choice(
        conn.execute("SELECT depot, workshop_bays, bays_free_today FROM depot_capacity").fetchall()
    )
    new_free = max(0, min(bays, free + rng.choice([-1, 1])))
    conn.execute(
        "UPDATE depot_capacity SET bays_free_today = ? WHERE depot = ?",
        (new_free, depot),
    )
    return f"depot '{depot}' bays free {free} → {new_free}"


def next_ticket_number(inbox: Path) -> int:
    highest = 0
    for d in (inbox, inbox.parent / "done"):
        if d.is_dir():
            for f in d.glob("TICKET-*.md"):
                m = re.match(r"TICKET-(\d+)", f.name)
                if m:
                    highest = max(highest, int(m.group(1)))
    return highest + 1


def write_ticket(inbox: Path, rng: random.Random, counter: int) -> str:
    template = TICKET_TEMPLATES[counter % len(TICKET_TEMPLATES)]
    ticket_id = f"TICKET-{next_ticket_number(inbox):04d}"
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / f"{ticket_id}.md"
    path.write_text(
        f"---\nid: {ticket_id}\ntype: {template['type']}\n"
        f"created: {date.today().isoformat()}\n---\n\n"
        f"# {template['title']}\n\n"
        + template["body"].format(ticket_id=ticket_id),
        encoding="utf-8",
    )
    return f"{ticket_id} dropped in inbox/ ({template['type']})"


def run_tick(db: Path, rng: random.Random, tickets: bool, inbox: Path,
             tick_no: int, force_duplicate: bool = False) -> list[str]:
    for attempt in (1, 2):
        events: list[str] = []  # a rolled-back attempt must not leave phantom events behind
        try:
            with connect(db) as conn:
                if force_duplicate:
                    events.append(insert_duplicate(conn, rng))
                else:
                    if rng.random() < 0.7:
                        events.append(insert_incident(conn, rng))
                    if rng.random() < 0.5:
                        events.append(insert_fuel(conn, rng))
                    if rng.random() < 0.4:
                        events.append(update_depot(conn, rng))
            break
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() and attempt == 1:
                time.sleep(0.5)
                continue
            raise
    if tickets and not force_duplicate and tick_no % 2 == 1:
        events.append(write_ticket(inbox, rng, tick_no // 2))
    if not events:
        events.append("quiet tick — nothing new")
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--interval", type=float, default=20, help="seconds between ticks (default 20)")
    parser.add_argument("--seed", type=int, default=42, help="deterministic event sequence (default 42)")
    parser.add_argument("--tickets", action="store_true", help="also drop work tickets in inbox/ every 2nd tick")
    parser.add_argument("--once", action="store_true", help="run exactly one tick, then exit")
    parser.add_argument("--duplicate", action="store_true", help="re-report the newest open incident once, then exit")
    parser.add_argument("--duration", type=parse_duration, default=None, help="auto-stop after e.g. 90s, 12m, 1h")
    parser.add_argument("--db", type=Path, default=DB_DEFAULT, help="path to fleet_ops.db")
    parser.add_argument("--inbox", type=Path, default=INBOX_DEFAULT, help="ticket inbox directory")
    args = parser.parse_args()

    rng = random.Random(args.seed if not args.duplicate else None)
    wait_for_db(args.db)

    events_total = 0
    tick_no = 0
    started = time.monotonic()
    seed_label = "none (duplicate mode)" if args.duplicate else str(args.seed)
    print(f"depot_sim: db={args.db} interval={args.interval:g}s seed={seed_label}"
          + (" tickets=on" if args.tickets else ""))
    try:
        while True:
            tick_no += 1
            events = run_tick(args.db, rng, args.tickets, args.inbox, tick_no,
                              force_duplicate=args.duplicate)
            stamp = time.strftime("%H:%M:%S")
            for event in events:
                print(f"[{stamp}] tick {tick_no:02d}: {event}", flush=True)
            events_total += len(events)
            if args.once or args.duplicate:
                break
            if args.duration is not None and time.monotonic() - started >= args.duration:
                print(f"[{stamp}] --duration reached, shift over.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\ndepot_sim: stopped.")
    print(f"depot_sim: {tick_no} ticks, {events_total} events injected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
