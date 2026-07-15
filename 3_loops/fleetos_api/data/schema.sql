-- FleetOS operational database (Challenge 5 copy).
-- This is the data the FleetOS API does NOT have: driver-reported incidents,
-- fuel/charging spend, and how many workshop bays each depot has free.
-- An agent that can join THIS with the maintenance API can answer questions
-- neither system can answer alone.
--
-- Challenge 5 note: seed dates are relative to date('now') so the incident
-- history always reads as recent — the depot simulator appends today's rows
-- next to these and the feed stays one continuous stream.
--
-- Rebuild: sqlite3 fleet_ops.db < schema.sql

DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS fuel_log;
DROP TABLE IF EXISTS depot_capacity;

CREATE TABLE incidents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id    TEXT    NOT NULL,
    reported_at   TEXT    NOT NULL,   -- ISO date
    reported_by   TEXT    NOT NULL,   -- driver name
    severity      TEXT    NOT NULL CHECK (severity IN ('low','medium','high')),
    category      TEXT    NOT NULL,   -- noise | warning_light | handling | bodywork | electrical
    description   TEXT    NOT NULL,
    resolved      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE fuel_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id    TEXT    NOT NULL,
    log_date      TEXT    NOT NULL,
    litres        REAL,               -- NULL for EVs
    kwh           REAL,               -- NULL for ICE
    cost_eur      REAL    NOT NULL,
    odometer_km   INTEGER NOT NULL
);

CREATE TABLE depot_capacity (
    depot              TEXT    PRIMARY KEY,
    workshop_bays      INTEGER NOT NULL,
    bays_free_today    INTEGER NOT NULL,
    region             TEXT    NOT NULL
);

-- ───────────────────────── Incidents ─────────────────────────
-- Deliberately overlaps with high-priority vehicles from the API so that
-- "overdue AND has open high-severity incident" returns interesting rows.
INSERT INTO incidents (vehicle_id, reported_at, reported_by, severity, category, description, resolved) VALUES
  ('VH-0017', date('now','-13 days'), 'S. Vogel',    'high',   'warning_light', 'Engine management light on since Monday, power feels reduced on inclines.', 0),
  ('VH-0017', date('now','-28 days'), 'S. Vogel',    'medium', 'noise',         'Intermittent rattle from rear suspension over cobbles.', 0),
  ('VH-0029', date('now','-7 days'),  'R. Schulz',   'high',   'handling',      'Pulls left under braking. Worse when loaded.', 0),
  ('VH-0126', date('now','-16 days'), 'K. Hofmann',  'medium', 'bodywork',      'Sliding door sticks, needs force to close fully.', 0),
  ('VH-0033', date('now','-5 days'),  'P. Neumann',  'low',    'noise',         'Squeak from dashboard area, cosmetic.', 0),
  ('VH-0023', date('now','-10 days'), 'I. Keller',   'medium', 'warning_light', 'Tyre pressure warning recurs after reset.', 0),
  ('VH-0064', date('now','-60 days'), 'L. Fischer',  'low',    'bodywork',      'Stone chip on windscreen, ~1cm, not in driver sightline.', 1),
  ('VH-0042', date('now','-4 days'),  'J. Brandt',   'low',    'electrical',    'USB charging port in cab intermittent.', 0),
  ('VH-0058', date('now','-24 days'), 'A. Lehmann',  'medium', 'electrical',    'Range estimate drops sharply below 20% — suspect battery cell imbalance.', 0),
  ('VH-0071', date('now','-96 days'), 'T. Roth',     'high',   'handling',      'ABS engaged unexpectedly on dry road.', 1),
  ('VH-0096', date('now','-3 days'),  'N. Hartmann', 'medium', 'noise',         'Whine from gearbox in 3rd gear under load.', 0),
  ('VH-0077', date('now','-14 days'), 'H. Winter',   'low',    'bodywork',      'Rear bumper scuff from loading dock.', 0);

-- ───────────────────────── Fuel / charging log ─────────────────────────
-- Enough rows to compute rough €/100km and spot the one anomalous vehicle.
INSERT INTO fuel_log (vehicle_id, log_date, litres, kwh, cost_eur, odometer_km) VALUES
  ('VH-0017', date('now','-26 days'), 72.4, NULL, 131.77, 154100),
  ('VH-0017', date('now','-12 days'), 75.1, NULL, 136.68, 155300),
  ('VH-0017', date('now','-3 days'),  78.9, NULL, 143.60, 156430),
  ('VH-0042', date('now','-21 days'), 58.0, NULL, 105.56, 82900),
  ('VH-0042', date('now','-6 days'),  56.3, NULL, 102.47, 84210),
  ('VH-0126', date('now','-18 days'), 80.2, NULL, 145.96, 140800),
  ('VH-0126', date('now','-5 days'),  81.5, NULL, 148.33, 142200),
  ('VH-0033', date('now','-14 days'), 63.7, NULL, 115.93, 130600),
  ('VH-0033', date('now','-4 days'),  62.9, NULL, 114.48, 131870),
  ('VH-0029', date('now','-31 days'), 49.8, NULL,  90.64, 176900),
  ('VH-0029', date('now','-9 days'),  68.2, NULL, 124.12, 178650),  -- consumption spike, correlates with brake incident
  ('VH-0071', date('now','-13 days'), 41.0, NULL,  74.62,  96700),
  ('VH-0071', date('now','-2 days'),  40.3, NULL,  73.35,  97540),
  ('VH-0023', date('now','-11 days'), 47.5, NULL,  86.45, 118900),
  ('VH-0023', date('now','-1 days'),  46.9, NULL,  85.36, 119870),
  ('VH-0064', date('now','-8 days'),  44.1, NULL,  80.26,  62800),
  ('VH-0096', date('now','-10 days'), 70.3, NULL, 127.95,  71500),
  ('VH-0096', date('now','-2 days'),  69.8, NULL, 127.04,  72440),
  ('VH-0058', date('now','-17 days'), NULL, 61.0,  27.45,  17900),
  ('VH-0058', date('now','-5 days'),  NULL, 64.0,  28.80,  18760),
  ('VH-0140', date('now','-7 days'),  NULL, 58.0,  26.10,   9120),
  ('VH-0077', date('now','-12 days'), 38.6, NULL,  70.25,  54900),
  ('VH-0077', date('now','-3 days'),  37.9, NULL,  68.98,  55630),
  ('VH-0103', date('now','-9 days'),  39.4, NULL,  71.71,  40500),
  ('VH-0112', date('now','-6 days'),  55.0, NULL, 100.10,  27540);

-- ───────────────────────── Depot capacity ─────────────────────────
INSERT INTO depot_capacity (depot, workshop_bays, bays_free_today, region) VALUES
  ('Hamburg Depot',                                     4, 2, 'North'),
  ('Munich North Logistics Hub - Gate 14',              3, 0, 'South'),
  ('Berlin Tempelhof',                                  2, 1, 'East'),
  ('Stuttgart Sued',                                    3, 1, 'South'),
  ('Erlangen Yard',                                    6, 4, 'Central'),
  ('Frankfurt Service Centre',                          5, 3, 'Central'),
  ('Krefeld Distribution Centre - Dock 3',    2, 0, 'Central'),
  ('Duesseldorf',                                       2, 2, 'West'),
  ('Leipzig Service Centre',                            4, 1, 'East'),
  ('Koeln Innenstadt',                                  1, 1, 'West'),
  ('Bremen Hafen',                                      3, 0, 'North'),
  ('Nuernberg Ost',                                     2, 2, 'South'),
  ('Dresden',                                           2, 1, 'East'),
  ('Hannover Messe - Hall 9',                           3, 2, 'North'),
  ('Dortmund',                                          2, 1, 'West'),
  ('Muenchen Service Centre',                           4, 3, 'South'),
  ('Essen',                                             2, 0, 'West');
