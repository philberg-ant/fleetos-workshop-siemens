#!/usr/bin/env python3
"""FleetOS dashboard acceptance checks — Challenge 5's referee.

Twelve deterministic checks over ../dashboard/ and the API on :8001.
Prints one [PASS]/[FAIL] line per check and a final "N/12 PASSED" line.
Exit code 0 only when all twelve pass.

This file is FROZEN: fix the dashboard, never the check.

Usage:
    python3 checks/check_dashboard.py
    python3 checks/check_dashboard.py --dashboard /path/to/dashboard --api http://localhost:8001
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

DASHBOARD_DEFAULT = Path(__file__).resolve().parents[2] / "dashboard"
API_DEFAULT = "http://localhost:8001"


def fetch_json(url: str):
    with urllib.request.urlopen(url, timeout=5) as res:
        return res.status, json.loads(res.read().decode("utf-8"))


def strip_comments(text: str) -> str:
    """Drop comments before substring checks, so a commented-out line can't
    satisfy a check: /* ... */ and <!-- ... --> blocks, plus whole-line //."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("//"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", type=Path, default=DASHBOARD_DEFAULT)
    parser.add_argument("--api", default=API_DEFAULT)
    args = parser.parse_args()

    dash = args.dashboard
    app_js = strip_comments((dash / "app.js").read_text(encoding="utf-8") if (dash / "app.js").exists() else "")
    index_html = strip_comments((dash / "index.html").read_text(encoding="utf-8") if (dash / "index.html").exists() else "")
    styles_css = strip_comments((dash / "styles.css").read_text(encoding="utf-8") if (dash / "styles.css").exists() else "")
    markup = app_js + "\n" + index_html

    results: list[tuple[str, str, bool, str]] = []  # (id, title, ok, detail)

    def check(check_id: str, title: str, ok: bool, detail: str = "") -> None:
        results.append((check_id, title, ok, detail))

    # ── C1: vehicle data is present and parseable ──────────────────────────
    vehicles = []
    try:
        vehicles = json.loads((dash / "data" / "vehicles.json").read_text(encoding="utf-8"))
        check("C1", "data/vehicles.json parses with 15+ records", len(vehicles) >= 15,
              f"found {len(vehicles)} records")
    except (OSError, json.JSONDecodeError) as exc:
        check("C1", "data/vehicles.json parses with 15+ records", False, str(exc))

    # ── C2: the API serves vehicles ────────────────────────────────────────
    try:
        status, body = fetch_json(f"{args.api}/vehicles")
        check("C2", "GET /vehicles returns 200 + JSON list",
              status == 200 and isinstance(body, list) and len(body) > 0,
              f"status {status}, {len(body) if isinstance(body, list) else '?'} records")
    except (OSError, json.JSONDecodeError) as exc:
        check("C2", "GET /vehicles returns 200 + JSON list", False,
              f"{exc} — is the API running? uvicorn --app-dir .. fleetos_api.main:app --port 8001")

    # ── C3: every status in the data appears in the UI ─────────────────────
    statuses = sorted({str(v.get("status", "")).lower() for v in vehicles if v.get("status")})
    missing = [s for s in statuses if s not in markup.lower()]
    check("C3", "every vehicle status in the data appears somewhere in the UI",
          bool(statuses) and not missing,
          ("statuses in data: " + ", ".join(statuses)
           + (f" — missing from app.js/index.html: {', '.join(missing)}."
              " If a status is never rendered, the summary cards can't add up to the total."
              if missing else "")))

    # ── C4: the incidents endpoint is wired into the frontend ──────────────
    c4_ok = "ops/incidents" in app_js
    check("C4", "app.js fetches the /ops/incidents endpoint", c4_ok,
          "" if c4_ok else
          "expected the string 'ops/incidents' in app.js — the Open Incidents card must read live data")

    # ── C5: the API serves incidents ───────────────────────────────────────
    try:
        status, body = fetch_json(f"{args.api}/ops/incidents")
        check("C5", "GET /ops/incidents returns 200 + JSON list",
              status == 200 and isinstance(body, list),
              f"status {status}, {len(body) if isinstance(body, list) else '?'} incidents")
    except (OSError, json.JSONDecodeError) as exc:
        check("C5", "GET /ops/incidents returns 200 + JSON list", False,
              f"{exc} — is the API running? uvicorn --app-dir .. fleetos_api.main:app --port 8001")

    # ── C6: the incidents count is not hardcoded markup ────────────────────
    m = re.search(r'id\s*=\s*["\']stat-incidents["\'][^>]*>\s*([^<]*?)\s*<', index_html)
    placeholder = m.group(1) if m else None
    hardcoded = placeholder is not None and re.fullmatch(r"\d+", placeholder) is not None
    check("C6", "the Open Incidents number comes from code, not hardcoded markup",
          (m is not None) and (not hardcoded or "stat-incidents" in app_js),
          (f"index.html ships the literal '{placeholder}' inside #stat-incidents and app.js never touches it"
           if hardcoded and "stat-incidents" not in app_js
           else "" if m else "no element with id=\"stat-incidents\" found in index.html"))

    # ── C7–C12: the Ops Feed card (built in Step 2) ─────────────────────────
    def hint(ok: bool, text: str) -> str:
        return "" if ok else text

    c7_ok = 'id="ops-feed"' in index_html
    check("C7", "index.html has an Ops Feed element (id=\"ops-feed\")", c7_ok,
          hint(c7_ok, "add a section with id=\"ops-feed\" — the surface Step 3's loop will write to"))

    c8_ok = "live/ops_status.json" in app_js
    check("C8", "app.js fetches live/ops_status.json", c8_ok,
          hint(c8_ok, "expected app.js to fetch './live/ops_status.json' (tip: use { cache: \"no-store\" } like the fleet data)"))

    c9_ok = (dash / "live").is_dir()
    check("C9", "dashboard/live/ directory exists", c9_ok,
          hint(c9_ok, "create dashboard/live/ — the loop writes ops_status.json there"))

    c10_ok = "updated_at" in app_js
    check("C10", "the Ops Feed renders the updated_at timestamp", c10_ok,
          hint(c10_ok, "expected app.js to reference 'updated_at' — the card must show when the loop last ran"))

    ops_snippet_start = app_js.find("ops_status")
    ops_region = app_js[max(0, ops_snippet_start - 500):ops_snippet_start + 1500] if ops_snippet_start >= 0 else ""
    c11_ok = ops_snippet_start >= 0 and ("catch" in ops_region or ".ok" in ops_region)
    check("C11", "the Ops Feed fails gracefully when ops_status.json is missing", c11_ok,
          hint(c11_ok, "the card must not break before the first loop run — handle fetch failure"
                       " and show a waiting message instead"))

    c12_ok = "ops-feed" in styles_css
    check("C12", "styles.css styles the Ops Feed", c12_ok,
          hint(c12_ok, "expected an .ops-feed (or #ops-feed) rule in styles.css"))

    passed = sum(1 for _, _, ok, _ in results if ok)
    for check_id, title, ok, detail in results:
        line = f"[{'PASS' if ok else 'FAIL'}] {check_id} — {title}"
        if detail and not ok:
            line += f"\n       ↳ {detail}"
        elif detail and ok:
            line += f"  ({detail})"
        print(line)
    print(f"\n{passed}/12 PASSED")
    return 0 if passed == 12 else 1


if __name__ == "__main__":
    sys.exit(main())
