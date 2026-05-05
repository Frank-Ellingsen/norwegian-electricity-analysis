import os
import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from requests.auth import HTTPBasicAuth

# =============================
# AUTO DATE (YESTERDAY)
# =============================
yesterday = datetime.now().date() - timedelta(days=1)

START_DATE = os.getenv("NO2_START_DATE", yesterday.strftime("%Y-%m-%d"))
END_DATE   = os.getenv("NO2_END_DATE",   yesterday.strftime("%Y-%m-%d"))

DB_NAME = "C:/Users/Lenovo/OneDrive/Desktop/datafrank/norwegian-electricity-analysis/NO2_forcasting/data/sqlite/no2_timeseries.db"

print(f"📅 Using dates: {START_DATE} → {END_DATE}")

# =============================
# AUTH
# =============================
FROST_CLIENT_ID = os.getenv("FROST_CLIENT_ID")
NVE_API_KEY     = os.getenv("NVE_API_KEY")

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
# SQLITE: schema + fast append (UPSERT)
# =============================
def init_db(conn: sqlite3.Connection):
    cur = conn.cursor()

    # Performance pragmas (safe defaults)
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")

    # Frost daily table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS obs_frost_daily (
        station_id   TEXT NOT NULL,
        time         TEXT NOT NULL,
        variable     TEXT NOT NULL,
        value        REAL,
        unit         TEXT,
        source       TEXT NOT NULL,
        PRIMARY KEY (station_id, time, variable)
    );
    """)

    # HydAPI daily table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS obs_hydapi_daily (
        station_id      TEXT NOT NULL,
        time            TEXT NOT NULL,
        parameter_id    TEXT NOT NULL,
        value           REAL,
        unit            TEXT,
        parameter_name  TEXT,
        target_name     TEXT,
        catchment       TEXT,
        source          TEXT NOT NULL,
        PRIMARY KEY (station_id, time, parameter_id)
    );
    """)

    # Optional: store resolved station mapping (so you don’t fuzzy-match every run if you want)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stations_hydapi_resolved (
        target_name   TEXT PRIMARY KEY,
        station_id    TEXT,
        matched_name  TEXT,
        match_score   REAL,
        catchment     TEXT,
        role          TEXT,
        updated_at    TEXT
    );
    """)

    conn.commit()


def upsert_many(conn: sqlite3.Connection, table: str, cols: list[str], rows: list[tuple], pk_cols: list[str], update_cols: list[str]):
    """
    Insert many rows using UPSERT:
      INSERT ... ON CONFLICT(pk) DO UPDATE SET ...
    Falls back to INSERT OR IGNORE if UPSERT is unavailable.
    """
    if not rows:
        print(f"⚠️ No rows to write -> {table}")
        return

    placeholders = ",".join(["?"] * len(cols))
    col_list = ",".join(cols)
    pk_list = ",".join(pk_cols)

    if update_cols:
        set_clause = ", ".join([f"{c}=excluded.{c}" for c in update_cols])
        sql = f"""
        INSERT INTO {table} ({col_list})
        VALUES ({placeholders})
        ON CONFLICT({pk_list}) DO UPDATE SET {set_clause};
        """
    else:
        # Do nothing on conflict
        sql = f"""
        INSERT INTO {table} ({col_list})
        VALUES ({placeholders})
        ON CONFLICT({pk_list}) DO NOTHING;
        """

    cur = conn.cursor()
    try:
        cur.executemany(sql, rows)
        conn.commit()
        print(f"✅ {table}: wrote {cur.rowcount if cur.rowcount != -1 else len(rows)} rows (UPSERT)")
    except sqlite3.OperationalError:
        # Fallback (older SQLite): ignore duplicates
        sql_fallback = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders});"
        cur.executemany(sql_fallback, rows)
        conn.commit()
        print(f"✅ {table}: wrote {cur.rowcount if cur.rowcount != -1 else len(rows)} rows (INSERT OR IGNORE fallback)")


# =============================
# HTTP
# =============================
def http_get(url, headers=None, params=None, auth=None, timeout=60):
    return requests.get(url, headers=headers, params=params, auth=auth, timeout=timeout)


# =============================
# FROST: DAILY OBSERVATIONS
# =============================
def fetch_frost_observations_daily():
    """
    Uses Frost observations endpoint with sources/elements/referencetime. [1](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
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

    print("\n🔍 Frost observations")
    print("Params:", params)

    r = http_get(endpoint, headers=FROST_HEADERS, params=params, auth=HTTPBasicAuth(FROST_CLIENT_ID, ""))
    print("Status:", r.status_code)

    if r.status_code != 200:
        print("❌ Frost error:", r.text[:500])
        return []

    out_rows = []
    for item in r.json().get("data", []):
        sid = item.get("sourceId")
        t   = item.get("referenceTime")
        for obs in item.get("observations", []):
            out_rows.append((
                sid,
                t,
                obs.get("elementId"),
                obs.get("value"),
                obs.get("unit"),
                "FROST"
            ))

    print(f"✅ Frost rows: {len(out_rows)}")
    return out_rows


# =============================
# HYDAPI: discovery + fetch
# =============================
def hydapi_fetch_all_stations_active():
    url = "https://hydapi.nve.no/api/v1/Stations"
    r = http_get(url, headers=HYD_HEADERS, params={"Active": 1})
    if r.status_code != 200:
        print("❌ HydAPI /Stations error:", r.text[:500])
        return pd.DataFrame()
    return pd.DataFrame(r.json().get("data", []))


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
    r = http_get(url, headers=HYD_HEADERS, params={"StationId": station_id})
    if r.status_code != 200:
        return [], r.status_code
    return r.json().get("data", []), 200


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


def fetch_hydapi_observations_daily(conn: sqlite3.Connection):
    """
    HydAPI Observations endpoint supports StationId, Parameter, ResolutionTime, ReferenceTime. [3](https://outlook.live.com/owa/?ItemID=AQMkADAwATExAGE2Ny00YzgxLTY3NTItMDACLTAwCgBGAAAD6ahiN8dkrkugORq4V%2bJQ8QcAtMNB9oN5zkiZV%2bbykqadjAAAAgEJAAAAtMNB9oN5zkiZV%2bbykqadjAAI808VxQAAAA%3d%3d&exvsurl=1&viewmodel=ReadMessageItem)[2](https://outlook.live.com/owa/?ItemID=AQMkADAwATExAGE2Ny00YzgxLTY3NTItMDACLTAwCgBGAAAD6ahiN8dkrkugORq4V%2bJQ8QcAtMNB9oN5zkiZV%2bbykqadjAAAAgEJAAAAtMNB9oN5zkiZV%2bbykqadjAAI91fj8AAAAA%3d%3d&exvsurl=1&viewmodel=ReadMessageItem)
    """
    obs_url = "https://hydapi.nve.no/api/v1/Observations"

    stations_df = hydapi_fetch_all_stations_active()
    param_map = hydapi_get_parameters_map()

    out_rows = []
    resolved_rows = []

    for t in HYDAPI_TARGETS:
        sid, matched_name, score = best_match_station_id(stations_df, t["name"])
        if not sid:
            print(f"⚠️ Could not resolve station for {t['name']}")
            continue

        print(f"✅ Resolved {t['name']} → {sid} (match='{matched_name}', score={score:.2f})")

        resolved_rows.append((
            t["name"], sid, matched_name, float(score), t["catchment"], t["role"], datetime.utcnow().isoformat()
        ))

        series_list, code = hydapi_get_series_for_station(sid)
        if code != 200:
            print(f"⚠️ No series for {sid}")
            continue

        pid = choose_parameter_for_station(series_list, param_map, t["role"])
        if not pid:
            print(f"⚠️ No parameter chosen for {sid}")
            continue

        pname = param_map.get(pid, {}).get("name", "")
        unit  = param_map.get(pid, {}).get("unit", "")

        params = {
            "StationId": sid,
            "Parameter": pid,
            "ResolutionTime": "1440",
            "ReferenceTime": f"{START_DATE}/{END_DATE}"
        }

        r = http_get(obs_url, headers=HYD_HEADERS, params=params)
        if r.status_code != 200:
            print(f"❌ HydAPI observations error for {sid}: {r.text[:200]}")
            continue

        for series in r.json().get("data", []):
            for o in series.get("observations", []):
                out_rows.append((
                    sid,
                    o.get("time"),
                    pid,
                    o.get("value"),
                    unit,
                    pname,
                    t["name"],
                    t["catchment"],
                    "HYDAPI"
                ))

    # Store resolved station mapping (append/upsert)
    if resolved_rows:
        upsert_many(
            conn,
            table="stations_hydapi_resolved",
            cols=["target_name","station_id","matched_name","match_score","catchment","role","updated_at"],
            rows=resolved_rows,
            pk_cols=["target_name"],
            update_cols=["station_id","matched_name","match_score","catchment","role","updated_at"]
        )

    print(f"✅ HydAPI rows: {len(out_rows)}")
    return out_rows


# =============================
# MAIN
# =============================
def main():
    print("🚀 Starting NO2 daily ingest (fast SQL append)")

    conn = sqlite3.connect(DB_NAME)
    init_db(conn)

    # --- Frost: fetch + UPSERT ---
    frost_rows = fetch_frost_observations_daily()
    upsert_many(
        conn,
        table="obs_frost_daily",
        cols=["station_id","time","variable","value","unit","source"],
        rows=frost_rows,
        pk_cols=["station_id","time","variable"],
        update_cols=["value","unit","source"]
    )

    # --- HydAPI: fetch + UPSERT ---
    hyd_rows = fetch_hydapi_observations_daily(conn)
    upsert_many(
        conn,
        table="obs_hydapi_daily",
        cols=["station_id","time","parameter_id","value","unit","parameter_name","target_name","catchment","source"],
        rows=hyd_rows,
        pk_cols=["station_id","time","parameter_id"],
        update_cols=["value","unit","parameter_name","target_name","catchment","source"]
    )

    conn.close()
    print("✅ Done (no overwrites, append/upsert only).")

if __name__ == "__main__":
    main()