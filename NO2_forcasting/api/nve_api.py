import os
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

NVE_API_KEY = os.getenv("NVE_API_KEY")
HYD_HEADERS = {"Accept": "application/json", "X-API-Key": NVE_API_KEY}

HYDAPI_TARGETS = [
    {"catchment": "Otra / Setesdal", "name": "Bykle",     "role": "snow"},
    {"catchment": "Setesdal",        "name": "Valle",     "role": "snow"},
    {"catchment": "Suldal",          "name": "Blåsjø",    "role": "discharge"},
    {"catchment": "Kvina",           "name": "Kvinesdal", "role": "discharge"},
    {"catchment": "Mandal",          "name": "Laudal",    "role": "discharge"},
]

def fetch_hydapi_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retrieves daily hydrology observations (snow/discharge) from NVE HydAPI.
    """
    if not NVE_API_KEY:
        logging.error("Missing NVE_API_KEY environment variable.")
        return pd.DataFrame()

    stations_url = "https://hydapi.nve.no/api/v1/Stations"
    params_url = "https://hydapi.nve.no/api/v1/Parameters"
    obs_url = "https://hydapi.nve.no/api/v1/Observations"

    try:
        # 1. Get Stations
        r_stations = requests.get(stations_url, headers=HYD_HEADERS, params={"Active": 1}, timeout=30)
        stations_df = pd.DataFrame(r_stations.json().get("data", []))
        
        # 2. Get Parameters
        r_params = requests.get(params_url, headers=HYD_HEADERS, timeout=30)
        param_map = {str(p.get("parameter", p.get("id"))): p for p in r_params.json().get("data", [])}

        out_rows = []
        for target in HYDAPI_TARGETS:
            # Simple fuzzy match for station
            best_sid, best_score = None, 0
            for _, row in stations_df.iterrows():
                score = SequenceMatcher(None, target["name"].lower(), str(row.get("stationName", "")).lower()).ratio()
                if score > best_score:
                    best_sid, best_score = row.get("stationId"), score
            
            if not best_sid or best_score < 0.6:
                continue

            # Get series for station to pick parameter
            r_series = requests.get("https://hydapi.nve.no/api/v1/Series", headers=HYD_HEADERS, params={"StationId": best_sid}, timeout=30)
            avail_pids = [str(s.get("parameter", s.get("parameterId"))) for s in r_series.json().get("data", [])]
            
            pid = None
            if target["role"] == "discharge":
                pid = "1001" if "1001" in avail_pids else (avail_pids[0] if avail_pids else None)
            else: # snow
                pid = next((p for p in avail_pids if "snø" in param_map.get(p, {}).get("name", "").lower()), avail_pids[0] if avail_pids else None)

            if not pid:
                continue

            # Fetch observations
            obs_params = {
                "StationId": best_sid,
                "Parameter": pid,
                "ResolutionTime": "1440",
                "ReferenceTime": f"{start_date}/{end_date}"
            }
            r_obs = requests.get(obs_url, headers=HYD_HEADERS, params=obs_params, timeout=30)
            
            for series in r_obs.json().get("data", []):
                for o in series.get("observations", []):
                    out_rows.append({
                        "station_id": best_sid,
                        "timestamp": o.get("time"),
                        "parameter_id": pid,
                        "value": o.get("value"),
                        "target_name": target["name"],
                        "role": target["role"]
                    })

        return pd.DataFrame(out_rows)

    except Exception as e:
        logging.error(f"Error fetching HydAPI data: {e}")
        return pd.DataFrame()

def save_hydapi_data(df: pd.DataFrame, output_path: str):
    """
    Appends HydAPI data to CSV, ensuring no duplicates.
    """
    if df.empty:
        return

    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(df)} HydAPI rows to new file {output_path}")

if __name__ == "__main__":
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    df = fetch_hydapi_data(yesterday, yesterday)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(base_path, "data", "hydrology_no2.csv")
    
    if not df.empty:
        save_hydapi_data(df, output_file)
