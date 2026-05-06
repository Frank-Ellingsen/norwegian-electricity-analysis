import os
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FROST_CLIENT_ID = os.getenv("FROST_CLIENT_ID")
FROST_HEADERS = {"User-Agent": "no2-model/1.0 (contact: frankellingsen@hotmail.com)"}

FROST_STATIONS = [
    {"station_id": "SN39100", "label": "Kristiansand – Kjevik"},
    {"station_id": "SN47450", "label": "Hovden i Setesdal"},
    {"station_id": "SN47600", "label": "Valle i Setesdal"},
    {"station_id": "SN46610", "label": "Åseral"},
    {"station_id": "SN44640", "label": "Liknes"},
]

def fetch_met_observations(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retrieves daily temperature and precipitation observations from MET Norway (Frost API).
    """
    if not FROST_CLIENT_ID:
        logging.error("Missing FROST_CLIENT_ID environment variable.")
        return pd.DataFrame()

    endpoint = "https://frost.met.no/observations/v0.jsonld"
    sources = ",".join([s["station_id"] for s in FROST_STATIONS])
    
    params = {
        "sources": sources,
        "elements": "mean(air_temperature P1D),sum(precipitation_amount P1D)",
        "referencetime": f"{start_date}/{end_date}",
        "timeoffsets": "default",
        "levels": "default",
        "qualities": "0,1,2,3",
    }

    logging.info(f"Fetching MET observations for {start_date} to {end_date}")
    try:
        r = requests.get(endpoint, headers=FROST_HEADERS, params=params, auth=HTTPBasicAuth(FROST_CLIENT_ID, ""), timeout=60)
        r.raise_for_status()
        
        data = r.json().get("data", [])
        out_rows = []
        for item in data:
            sid = item.get("sourceId")
            t   = item.get("referenceTime")
            for obs in item.get("observations", []):
                out_rows.append({
                    "station_id": sid,
                    "timestamp": t,
                    "variable": obs.get("elementId"),
                    "value": obs.get("value"),
                    "unit": obs.get("unit")
                })
        
        return pd.DataFrame(out_rows)

    except Exception as e:
        logging.error(f"Error fetching MET data: {e}")
        return pd.DataFrame()

def save_met_data(df: pd.DataFrame, output_path: str):
    """
    Appends MET data to CSV, ensuring no duplicates.
    """
    if df.empty:
        return

    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['station_id', 'timestamp', 'variable'], keep='last')
        combined_df.to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    logging.info(f"Saved {len(df)} MET rows to {output_path}")

if __name__ == "__main__":
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    df = fetch_met_observations(yesterday, yesterday)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(base_path, "data", "weather_no2.csv")
    
    if not df.empty:
        save_met_data(df, output_file)
