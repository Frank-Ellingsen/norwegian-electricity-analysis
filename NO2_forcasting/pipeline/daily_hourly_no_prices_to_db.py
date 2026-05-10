# daily_hourly_no_prices_to_db
# Runs once per day
# Automatically uses yesterday’s date
# Fetches hourly prices (HH:00 only)
# Inserts exactly 24 rows per zone
# Skips zones with incomplete data
# Is safe to run repeatedly (idempotent)
# This script is meant to be run via cron / systemd timer / task scheduler.

import requests
import pandas as pd
import os
import logging
from datetime import date, timedelta
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
ZONES = ["NO1", "NO2", "NO3", "NO4", "NO5"]

# Define the output directory for CSV files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "data", "ingested_prices")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
# FETCH, FILTER, GROUP BY ZONE
# -------------------------------------------------
rows_by_zone = defaultdict(list)

logging.info(f"🚀 Starting daily ingestion for {TARGET_DATE}...")

for zone in ZONES:
    url = (
        f"https://spot.utilitarian.io/electricity/"
        f"{zone}/{TARGET_DATE.year}/"
        f"{TARGET_DATE.month:02d}/"
        f"{TARGET_DATE.day:02d}/"
    )

    try:
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
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error fetching data for zone {zone} from {url}: {e}")
        continue

# -------------------------------------------------
# VALIDATE COMPLETE DAYS (24 HOURS)
# -------------------------------------------------
rows_to_insert = []

logging.info(f"\nDaily import for {TARGET_DATE}:\n")

for zone, rows in rows_by_zone.items():
    if len(rows) == 24:
        rows_to_insert.extend(rows)
        logging.info(f"✅ {zone}: 24 hourly rows — OK")
    else:
        logging.warning(f"❌ {zone}: {len(rows)} rows — SKIPPED (incomplete day)")

logging.info(f"\nTotal rows prepared for CSV: {len(rows_to_insert)}")

# -------------------------------------------------
# WRITE TO CSV (IDEMPOTENT - OVERWRITES FOR THE DAY)
# -------------------------------------------------
if rows_to_insert:
    df = pd.DataFrame(rows_to_insert, columns=['zone', 'timestamp', 'price_eur_per_mwh'])
    
    # Define the CSV file path
    output_file = os.path.join(OUTPUT_DIR, f"{TARGET_DATE.strftime('%Y-%m-%d')}_electricity_prices.csv")
    
    try:
        df.to_csv(output_file, index=False)
        logging.info(f"✅ Successfully wrote {len(rows_to_insert)} rows to {output_file}")
    except Exception as e:
        logging.error(f"❌ Error writing data to CSV file {output_file}: {e}")
else:
    logging.warning(f"⚠️ No data to write for {TARGET_DATE}.")

logging.info("✨ Done.")
