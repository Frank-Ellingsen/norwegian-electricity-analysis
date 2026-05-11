import os
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================
# GLOBAL CONFIG / HELPERS
# =============================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================
# AUTH
# =============================
FROST_CLIENT_ID = os.getenv("FROST_CLIENT_ID")
NVE_API_KEY     = os.getenv("NVE_API_KEY")

# These checks should be done once when the module is imported or when main is called
# For now, keeping them global as they were, but better to move into main or a setup function.
if not FROST_CLIENT_ID:
    raise RuntimeError("Missing env var FROST_CLIENT_ID")
if not NVE_API_KEY:
    raise RuntimeError("Missing env var NVE_API_KEY")

FROST_HEADERS = {"User-Agent": "no2-model/1.0 (contact: frankellingsen@hotmail.com)"}
HYD_HEADERS   = {"Accept": "application/json", "X-API-Key": NVE_API_KEY}

# =============================
# STATIONS
# =============================
FROST_STATIONS = [
    {"station_id": "SN39100", "label": "Kristiansand – Kjevik"},
    {"station_id": "SN47450", "label": "Hovden i Setesdal"},
    {"station_id": "SN47600", "label": "Valle i Setesdal"},
    {"station_id": "SN46610", "label": "Åseral"},
    {"station_id": "SN44640", "label": "Liknes"},
]

HYDAPI_TARGETS = [
    {"catchment": "Otra / Setesdal", "name": "Bykle",     "role": "snow"},
    {"catchment": "Setesdal",        "name": "Valle",     "role": "snow"},
    {"catchment": "Suldal",          "name": "Blåsjø",    "role": "discharge"},
    {"catchment": "Kvina",           "name": "Kvinesdal", "role": "discharge"},
    {"catchment": "Mandal",          "name": "Laudal",    "role": "discharge"},
]

# =============================
# HTTP
# =============================
def http_get(url, headers=None, params=None, auth=None, timeout=60):
    return requests.get(url, headers=headers, params=params, auth=auth, timeout=timeout)


# =============================
# FROST: DAILY OBSERVATIONS
# =============================
def fetch_frost_observations_daily(start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """
    Fetches Frost observations, processes them into temperature and precipitation,
    and returns a DataFrame ready for CSV export.
    """
    endpoint = "https://frost.met.no/observations/v0.jsonld"

    sources = ",".join([s["station_id"] for s in FROST_STATIONS])
    params = {
        "sources": sources,
        "elements": "mean(air_temperature P1D),sum(precipitation_amount P1D)",
        "referencetime": f"{start_date_str}/{end_date_str}",
        "timeoffsets": "default",
        "levels": "default",
        "qualities": "0,1,2,3",
    }
    logging.info("\n🔍 Fetching Frost observations")
    logging.info(f"Params: {params}")

    try:
        r = http_get(endpoint, headers=FROST_HEADERS, params=params, auth=HTTPBasicAuth(FROST_CLIENT_ID, ""))
        r.raise_for_status()
        
        raw_data = r.json().get("data", [])
        
        processed_rows = []
        for item in raw_data:
            station_id = item.get("sourceId")
            observation_time = item.get("referenceTime")
            
            temperature_val = None
            precipitation_val = None
            
            for obs in item.get("observations", []):
                variable = obs.get("elementId")
                value = obs.get("value")
                
                if variable == "mean(air_temperature P1D)":
                    temperature_val = value
                elif variable == "sum(precipitation_amount P1D)":
                    precipitation_val = value
            
            if temperature_val is not None or precipitation_val is not None:
                processed_rows.append({
                    "station_id": station_id,
                    "time": observation_time,
                    "temperature": temperature_val,
                    "precipitation": precipitation_val,
                    "source": "FROST"
                })
        
        df_frost = pd.DataFrame(processed_rows)
        logging.info(f"✅ Frost observations structured. Rows fetched: {len(df_frost)}")
        return df_frost

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Frost API error: {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred while fetching Frost data: {e}")
        return pd.DataFrame()


# =============================
# HYDAPI: discovery + fetch helpers
# =============================
def best_match_station_id(stations_df: pd.DataFrame, target_name: str):
    if stations_df.empty or "stationName" not in stations_df.columns:
        return None, None, 0.0

    t = target_name.lower().strip()
    best_sid, best_name, best_score = None, None, 0.0

    for _, row in stations_df.iterrows():
        name = str(row.get("stationName", "")).lower()
        sid  = row.get("stationId")
        if not sid or not name:
            continue

        score = SequenceMatcher(None, t, name).ratio()
        if score > best_score:
            best_sid, best_name, best_score = sid, row.get("stationName"), score

    return best_sid, best_name, best_score


def hydapi_get_parameters_map():
    url = "https://hydapi.nve.no/api/v1/Parameters"
    r = http_get(url, headers=HYD_HEADERS)
    if r.status_code != 200:
        logging.error(f"❌ HydAPI /Parameters error: {r.text[:500]}") # Changed print to logging.error
        return {}

    param_map = {}
    for p in r.json().get("data", []):
        pid = p.get("parameter") if p.get("parameter") is not None else p.get("id")
        if pid is None:
            continue
        pid = str(pid)
        param_map[pid] = {"name": p.get("name", ""), "unit": p.get("unit", "")}
    return param_map


def hydapi_get_series_for_station(station_id: str):
    url = "https://hydapi.nve.no/api/v1/Series"
    try:
        r = http_get(url, headers=HYD_HEADERS, params={"StationId": station_id})
        r.raise_for_status()
        return r.json().get("data", []), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ HydAPI /Series error for station {station_id}: {e}")
        return [], 500


def choose_parameter_for_station(series_list, param_map, role: str):
    avail = []
    for s in series_list:
        pid = s.get("parameter") if s.get("parameter") is not None else s.get("parameterId")
        if pid is None:
            continue
        avail.append(str(pid))
    avail = sorted(set(avail))
    if not avail:
        return None

    def pname(pid):
        return (param_map.get(pid, {}).get("name") or "").lower()

    if role == "discharge":
        if "1001" in avail:
            return "1001"
        for pid in avail:
            n = pname(pid)
            if "vannfør" in n or "discharge" in n:
                return pid
        return avail[0]

    if role == "snow":
        for pid in avail:
            n = pname(pid)
            if "snø" in n or "snow" in n or "swe" in n:
                return pid
        return avail[0]

    return avail[0]


def hydapi_fetch_all_stations_active():
    url = "https://hydapi.nve.no/api/v1/Stations"
    params = {"Active": True}
    try:
        r = http_get(url, headers=HYD_HEADERS, params=params)
        r.raise_for_status()
        return pd.DataFrame(r.json().get("data", []))
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ HydAPI /Stations error: {e}")
        return pd.DataFrame()

def fetch_hydapi_observations_daily(start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """
    HydAPI Observations endpoint supports StationId, Parameter, ResolutionTime, ReferenceTime.
    Returns:
        pd.DataFrame: DataFrame containing HydAPI observations.
    """
    obs_url = "https://hydapi.nve.no/api/v1/Observations"

    stations_df = hydapi_fetch_all_stations_active()
    param_map = hydapi_get_parameters_map()

    out_rows = []
    logging.info("\n🔍 Fetching HydAPI observations")
    for t in HYDAPI_TARGETS:
        sid, matched_name, score = best_match_station_id(stations_df, t["name"])
        if not sid:
            logging.warning(f"⚠️ Could not resolve station for {t['name']}")
            continue

        logging.info(f"✅ Resolved {t['name']} → {sid} (match='{matched_name}', score={score:.2f})")

        series_list, code = hydapi_get_series_for_station(sid)
        if code != 200:
            logging.warning(f"⚠️ No series for {sid}")
            continue

        pid = choose_parameter_for_station(series_list, param_map, t["role"])
        if not pid:
            logging.warning(f"⚠️ No parameter chosen for {sid}")
            continue

        pname = param_map.get(pid, {}).get("name", "")
        unit  = param_map.get(pid, {}).get("unit", "")

        params = {
            "StationId": sid,
            "Parameter": pid,
            "ResolutionTime": "1440",
            "ReferenceTime": f"{start_date_str}/{end_date_str}"
        }

        try:
            r = http_get(obs_url, headers=HYD_HEADERS, params=params)
            r.raise_for_status()

            for series in r.json().get("data", []):
                for o in series.get("observations", []):
                    out_rows.append({
                        "station_id": sid,
                        "time": o.get("time"),
                        "parameter_id": pid,
                        "value": o.get("value"),
                        "unit": unit,
                        "parameter_name": pname,
                        "target_name": t["name"],
                        "catchment": t["catchment"],
                        "source": "HYDAPI"
                    })
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ HydAPI observations error for {sid}: {e}")
            continue
        except Exception as e:
            logging.error(f"❌ An unexpected error occurred while fetching HydAPI data for {sid}: {e}")
            continue

    df_hydapi = pd.DataFrame(out_rows)
    logging.info(f"✅ HydAPI rows fetched: {len(df_hydapi)}")
    return df_hydapi


def main(start_date: str = None, end_date: str = None):
    # Configure logging here to ensure it's set up when main is called
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    yesterday = datetime.now().date() - timedelta(days=1)
    
    if start_date is None:
        start_date = os.getenv("NO2_START_DATE", yesterday.strftime("%Y-%m-%d"))
    if end_date is None:
        end_date = os.getenv("NO2_END_DATE", yesterday.strftime("%Y-%m-%d"))

    logging.info(f"📅 Using dates: {start_date} → {end_date}")

    FROST_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "data", "ingested_weather")
    HYDAPI_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "data", "ingested_weather")
    os.makedirs(FROST_OUTPUT_DIR, exist_ok=True)
    # os.makedirs(HYDAPI_OUTPUT_DIR, exist_ok=True) # This is redundant as FROST_OUTPUT_DIR is the same

    # --- Frost: fetch and save to CSV ---
    frost_df = fetch_frost_observations_daily(start_date, end_date)
    if not frost_df.empty:
        output_file = os.path.join(FROST_OUTPUT_DIR, f"{start_date}_frost_weather.csv") # Renamed for clarity
        try:
            frost_df.to_csv(output_file, index=False)
            logging.info(f"✅ Frost weather data saved to {output_file}")
        except Exception as e:
            logging.error(f"❌ Error saving Frost weather data to CSV: {e}")
    else:
        logging.warning("⚠️ No Frost weather data to save.")

    # --- HydAPI: fetch and save to CSV ---
    hydapi_df = fetch_hydapi_observations_daily(start_date, end_date)
    if not hydapi_df.empty:
        output_file = os.path.join(HYDAPI_OUTPUT_DIR, f"{start_date}_hydapi_weather.csv") # Renamed for clarity
        try:
            hydapi_df.to_csv(output_file, index=False)
            logging.info(f"✅ HydAPI data saved to {output_file}")
        except Exception as e:
            logging.error(f"❌ Error saving HydAPI data to CSV: {e}")
    else:
        logging.warning("⚠️ No HydAPI data to save.")

    logging.info("✨ Done.")

if __name__ == "__main__":
    main()
