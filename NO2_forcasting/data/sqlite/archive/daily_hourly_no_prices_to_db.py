# daily_hourly_no_prices_to_db
# Runs once per day
# Automatically uses yesterday’s date
# Fetches hourly prices (HH:00 only)
# Inserts exactly 24 rows per zone
# Skips zones with incomplete data
# Is safe to run repeatedly (idempotent)
# This script is meant to be run via cron / systemd timer / task scheduler.

import requests
import sqlite3
from datetime import date, timedelta
from collections import defaultdict

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
ZONES = ["NO1", "NO2", "NO3", "NO4", "NO5"]
DB_FILE = DB_FILE = r"C:\Users\Lenovo\OneDrive\Desktop\datafrank\norwegian-electricity-analysis\NO2_forcasting\data\sqlite\electricity_prices_no.db"

# ✅ Always process YESTERDAY
TARGET_DATE = date.today() - timedelta(days=1)

# -------------------------------------------------
# HELPER: hourly-only filter
# -------------------------------------------------
def is_full_hour(timestamp: str) -> bool:
    """
    Save ONLY timestamps that contain ':00:'
    """
    return ":00:" in timestamp

# -------------------------------------------------
# DATABASE SETUP
# -------------------------------------------------
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS electricity_prices_daily (
    zone TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    price_eur_per_mwh REAL NOT NULL,
    CHECK (substr(timestamp, 15, 2) = '00'),
    PRIMARY KEY (zone, timestamp)
)
""")

# -------------------------------------------------
# FETCH, FILTER, GROUP BY ZONE
# -------------------------------------------------
rows_by_zone = defaultdict(list)

for zone in ZONES:
    url = (
        f"https://spot.utilitarian.io/electricity/"
        f"{zone}/{TARGET_DATE.year}/"
        f"{TARGET_DATE.month:02d}/"
        f"{TARGET_DATE.day:02d}/"
    )

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    for entry in data:
        ts = entry["timestamp"]

        if not is_full_hour(ts):
            continue

        rows_by_zone[zone].append(
            (zone, ts, float(entry["value"]))
        )

# -------------------------------------------------
# VALIDATE COMPLETE DAYS (24 HOURS)
# -------------------------------------------------
rows_to_insert = []

print(f"\nDaily import for {TARGET_DATE}:\n")

for zone, rows in rows_by_zone.items():
    if len(rows) == 24:
        rows_to_insert.extend(rows)
        print(f"✅ {zone}: 24 hourly rows — OK")
    else:
        print(f"❌ {zone}: {len(rows)} rows — SKIPPED")

print(f"\nTotal rows prepared for insert: {len(rows_to_insert)}")

# -------------------------------------------------
# INSERT INTO SQLITE (IDEMPOTENT)
# -------------------------------------------------
cursor.executemany("""
INSERT OR IGNORE INTO electricity_prices_daily (
    zone,
    timestamp,
    price_eur_per_mwh
) VALUES (?, ?, ?)
""", rows_to_insert)

conn.commit()

print(f"Rows inserted into DB: {cursor.rowcount}")
print("Done.")

conn.close()
