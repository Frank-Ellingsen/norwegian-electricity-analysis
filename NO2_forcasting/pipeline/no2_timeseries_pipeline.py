import os
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# =============================
# AUTO DATE (YESTERDAY)
# =============================
yesterday = datetime.now().date() - timedelta(days=1)

START_DATE = os.getenv("NO2_START_DATE", yesterday.strftime("%Y-%m-%d"))
END_DATE   = os.getenv("NO2_END_DATE",   yesterday.strftime("%Y-%m-%d"))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FROST_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "data", "ingested_frost")
HYDAPI_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "data", "ingested_hydapi")
os.makedirs(FROST_OUTPUT_DIR, exist_ok=True)
os.makedirs(HYDAPI_OUTPUT_DIR, exist_ok=True)


logging.info(f"📅 Using dates: {START_DATE} → {END_DATE}")

# =============================
# AUTH
# =============================
FROST_CLIENT_ID = os.getenv("FROST_CLIENT_ID")
NVE_API_KEY     = os.getenv("NVE_API_KEY")

if not FROST_CLIENT_ID:
    logging.error("Missing env var FROST_CLIENT_ID")
    raise RuntimeError("Missing env var FROST_CLIENT_ID")
if not NVE_API_KEY:
    logging.error("Missing env var NVE_API_KEY")
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
def fetch_frost_observations_daily() -> pd.DataFrame:
    """
    Uses Frost observations endpoint with sources/elements/referencetime.
    Returns:
        pd.DataFrame: DataFrame containing Frost observations.
    """
    endpoint = "https://frost.met.no/observations/v0.jsonld"

    sources = ",".join([s["station_id"] for s in FROST_STATIONS])
    params = {
        "sources": sources,
        "elements": "mean(air_temperature P1D),sum(precipitation_amount P1D)",
        "referencetime": f"{START_DATE}/{END_DATE}",
        "timeoffsets": "default",
        "levels": "default",
        "qualities": "0,1,2,3",
    }

    logging.info("\n🔍 Fetching Frost observations")
    logging.info(f"Params: {params}")

    try:
        r = http_get(endpoint, headers=FROST_HEADERS, params=params, auth=HTTPBasicAuth(FROST_CLIENT_ID, ""))
        r.raise_for_status()
        
        out_rows = []
        for item in r.json().get("data", []):
            sid = item.get("sourceId")
            t   = item.get("referenceTime")
            for obs in item.get("observations", []):
                out_rows.append({
                    "station_id": sid,
                    "time": t,
                    "variable": obs.get("elementId"),
                    "value": obs.get("value"),
                    "unit": obs.get("unit"),
                    "source": "FROST"
                })
        
        df_frost = pd.DataFrame(out_rows)
        logging.info(f"✅ Frost rows fetched: {len(df_frost)}")
        return df_frost

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Frost API error: {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred while fetching Frost data: {e}")
        return pd.DataFrame()


# =============================
# HYDAPI: discovery + fetch
# =============================
def hydapi_fetch_all_stations_active() -> pd.DataFrame:
    url = "https://hydapi.nve.no/api/v1/Stations"
    try:
        r = http_get(url, headers=HYD_HEADERS, params={"Active": 1})
        r.raise_for_status()
        return pd.DataFrame(r.json().get("data", []))
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ HydAPI /Stations error: {e}")
        return pd.DataFrame()



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
    """
    HydAPI /Parameters exists and returns parameter metadata. [2](https://outlook.live.com/owa/?ItemID=AQMkADAwATExAGE2Ny00YzgxLTY3NTItMDACLTAwCgBGAAAD6ahiN8dkrkugORq4V%2bJQ8QcAtMNB9oN5zkiZV%2bbykqadjAAAAgEJAAAAtMNB9oN5zkiZV%2bbykqadjAAI91fj8AAAAA%3d%3d&exvsurl=1&viewmodel=ReadMessageItem)[3](https://outlook.live.com/owa/?ItemID=AQMkADAwATExAGE2Ny00YzgxLTY3NTItMDACLTAwCgBGAAAD6ahiN8dkrkugORq4V%2bJQ8QcAtMNB9oN5zkiZV%2bbykqadjAAAAgEJAAAAtMNB9oN5zkiZV%2bbykqadjAAI808VxQAAAA%3d%3d&exvsurl=1&viewmodel=ReadMessageItem)
    """
    url = "https://hydapi.nve.no/api/v1/Parameters"
    r = http_get(url, headers=HYD_HEADERS)
    if r.status_code != 200:
        print("❌ HydAPI /Parameters error:", r.text[:500])
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


def fetch_hydapi_observations_daily() -> pd.DataFrame:
    """
    HydAPI Observations endpoint supports StationId, Parameter, ResolutionTime, ReferenceTime.
    Returns:
        pd.DataFrame: DataFrame containing HydAPI observations.
    """
    obs_url = "https://hydapi.nve.no/api/v1/Observations"

    stations_df = hydapi_fetch_all_stations_active()
    param_map = hydapi_get_parameters_map()

    out_rows = []
    # Resolved rows are not persisted to CSV for now, as per the decision in previous step.
    # If needed, this could be stored in a separate static CSV.

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
            "ReferenceTime": f"{START_DATE}/{END_DATE}"
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


# =============================
# MAIN
# =============================
def main():
    logging.info("🚀 Starting NO2 daily exogenous data ingest (to CSV)")

    # --- Frost: fetch and save to CSV ---
    frost_df = fetch_frost_observations_daily()
    if not frost_df.empty:
        output_file = os.path.join(FROST_OUTPUT_DIR, f"{START_DATE}_frost_observations.csv")
        try:
            frost_df.to_csv(output_file, index=False)
            logging.info(f"✅ Frost observations saved to {output_file}")
        except Exception as e:
            logging.error(f"❌ Error saving Frost observations to CSV: {e}")
    else:
        logging.warning("⚠️ No Frost observations to save.")

    # --- HydAPI: fetch and save to CSV ---
    hydapi_df = fetch_hydapi_observations_daily()
    if not hydapi_df.empty:
        output_file = os.path.join(HYDAPI_OUTPUT_DIR, f"{START_DATE}_hydapi_observations.csv")
        try:
            hydapi_df.to_csv(output_file, index=False)
            logging.info(f"✅ HydAPI observations saved to {output_file}")
        except Exception as e:
            logging.error(f"❌ Error saving HydAPI observations to CSV: {e}")
    else:
        logging.warning("⚠️ No HydAPI observations to save.")

    logging.info("✨ Done.")

if __name__ == "__main__":
    main()