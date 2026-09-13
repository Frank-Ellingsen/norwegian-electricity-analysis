import os
import sqlite3
import logging
import pandas as pd
from datetime import datetime
from entsoe import EntsoeRawClient
import requests
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_DIR = "data/NO_EL_PRICES"
DATABASE_NAME = os.path.join(DATABASE_DIR, "NO_EL_PRICES.db")

# Environment Variables
ENTSOE_TOKEN = os.environ.get("ENTSOE_TOKEN")
FROST_CLIENT_ID = os.environ.get("FROST_CLIENT_ID")

# Bidding Zones Mapping
BIDDING_ZONES = {
    "NO1": "10YNO-1--------2",
    "NO2": "10YNO-2--------T",
    "NO3": "10YNO-3--------J",
    "NO4": "10YNO-4--------9",
    "NO5": "10Y1001A1001A48H"
}

def insert_prices(data, zone):
    """Inserts electricity prices into SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Assuming data is a list of dicts: {'time_start': ..., 'price': ...}
    for entry in data:
        cursor.execute("""
            INSERT OR IGNORE INTO electricity_prices (time_start, time_end, price_nok_per_kwh, price_area, date_retrieved)
            VALUES (?, ?, ?, ?, ?)
        """, (entry['start'], entry['end'], entry['price'], zone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def parse_entsoe_xml(xml_string, zone):
    """Parses ENTSO-E XML prices."""
    # Simplified parsing for demonstration
    root = ET.fromstring(xml_string)
    prices = []
    # This needs to be tailored to the specific XML structure of ENTSO-E
    # ... logic ...
    return prices

def fetch_entsoe_prices(start_date, end_date):
    """Fetches day-ahead prices from ENTSO-E."""
    if not ENTSOE_TOKEN:
        logging.error("ENTSOE_TOKEN not set.")
        return
    
    client = EntsoeRawClient(api_key=ENTSOE_TOKEN)
    
    for zone, eic in BIDDING_ZONES.items():
        logging.info(f"Fetching ENTSO-E data for {zone}...")
        try:
            xml_data = client.query_day_ahead_prices(eic, start=pd.Timestamp(start_date, tz='UTC'), end=pd.Timestamp(end_date, tz='UTC'))
            prices = parse_entsoe_xml(xml_data, zone)
            insert_prices(prices, zone)
            logging.info(f"Successfully fetched and inserted ENTSO-E data for {zone}.")
        except Exception as e:
            logging.error(f"Error fetching ENTSO-E data for {zone}: {e}")
            
def insert_weather(data):
    """Inserts weather data into SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # ... insertion logic ...
    conn.commit()
    conn.close()

def fetch_frost_weather(start_date, end_date):
    """Fetches weather data from Frost."""
    if not FROST_CLIENT_ID:
        logging.error("FROST_CLIENT_ID not set.")
        return
        
    endpoint = 'https://frost.met.no/observations/v0.jsonld'
    parameters = {
        'sources': 'SN18700',
        'elements': 'mean(air_temperature P1D)',
        'referencetime': f'{start_date.strftime("%Y-%m-%d")}/{end_date.strftime("%Y-%m-%d")}',
    }
    
    logging.info("Fetching Frost weather data...")
    r = requests.get(endpoint, parameters, auth=(FROST_CLIENT_ID, ''))
    if r.status_code == 200:
        data = r.json()
        insert_weather(data)
        logging.info("Successfully fetched and inserted Frost data.")
    else:
        logging.error(f"Frost API Error: {r.status_code}")

if __name__ == "__main__":
    start = datetime(2020, 1, 1)
    end = datetime(2026, 1, 1)
    
    # fetch_entsoe_prices(start, end)
    # fetch_frost_weather(start, end)
    logging.info("Script structure updated. XML/JSON parsing needs specific schema implementation.")
