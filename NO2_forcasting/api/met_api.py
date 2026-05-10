import requests
import pandas as pd
import logging
from datetime import datetime, timedelta

# Configuration from GEMINI.md for MET Norway
MET_API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
# NOTE: User-Agent header is required by MET API. In a production system, this should be more specific.
# For now, we use a generic one.
MET_API_HEADERS = {
    "User-Agent": "NO2_Forecasting_Project/1.0 (contact: your_email@example.com)"
}

def fetch_met_forecast(lat: float, lon: float, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Fetches weather forecast data from MET Norway API for a given location and time range.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        start_time: The start datetime for the forecast (inclusive).
        end_time: The end datetime for the forecast (inclusive).

    Returns:
        A pandas DataFrame containing forecast data, or an empty DataFrame if an error occurs.
    """
    logging.info(f"Fetching MET Norway forecast for lat={lat}, lon={lon} from {start_time} to {end_time}")

    # MET API typically returns forecast for the next ~10 days.
    # We need to adjust the request based on available forecast horizon.
    # The API might not support arbitrary start/end times for historical data,
    # it's primarily for forecasts. For this project, we assume we are fetching future forecasts.

    params = {
        "lat": lat,
        "lon": lon,
        "altitude": 0 # Assuming ground level, can be adjusted if elevation data is available
    }

    try:
        response = requests.get(MET_API_URL, headers=MET_API_HEADERS, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        
        forecast_data = []
        
        # Process the forecast data
        # The structure of the JSON response can be complex. We need to extract relevant fields.
        # Based on typical MET API responses:
        # 'properties' -> 'timeseries' is a list of forecast points
        for forecast_point in data['properties']['timeseries']:
            timestamp = datetime.fromisoformat(forecast_point['time']).replace(tzinfo=None) # Remove timezone info for consistency with project
            
            # Check if the timestamp falls within our desired range
            if start_time <= timestamp < end_time: # Use < end_time because end_time is typically exclusive for ranges
                current_weather = forecast_point['data']['instant']['details']
                
                # Extract required fields
                temperature = current_weather.get('air_temperature')
                wind_speed = current_point.get('wind_speed')
                precipitation = forecast_point['data'].get('next_1_hours', {}).get('precipitation') # precipitation is in next_1_hours

                forecast_data.append({
                    'timestamp': timestamp,
                    'temperature': temperature,
                    'wind_speed': wind_speed,
                    'precipitation': precipitation,
                })
        
        df_forecast = pd.DataFrame(forecast_data)
        
        if not df_forecast.empty:
            df_forecast = df_forecast.set_index('timestamp')
            logging.info(f"Successfully fetched {len(df_forecast)} forecast points from MET API.")
        else:
            logging.warning("No forecast data found within the specified time range from MET API.")
        
        return df_forecast

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching MET Norway forecast: {e}")
        return pd.DataFrame()
    except KeyError as e:
        logging.error(f"Error parsing MET Norway API response: Missing key {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"An unexpected error occurred during MET Norway API fetch: {e}")
        return pd.DataFrame()

# --- Example Usage ---
# This part is for demonstration and testing purposes.
# It should not be executed when the module is imported.
if __name__ == "__main__":
    # Example coordinates for Kristiansand, Norway (representative for NO2 bidding zone)
    example_lat = 58.1467
    example_lon = 7.9956

    # Fetch forecast for the next 48 hours
    now = datetime.utcnow().replace(tzinfo=None) # Ensure now is naive UTC for comparison
    start_forecast = now.replace(minute=0, second=0, microsecond=0)
    end_forecast = start_forecast + timedelta(hours=48)

    # Ensure start_time is not in the past for forecast API, adjust if necessary
    if start_forecast < now:
        start_forecast = now.replace(minute=0, second=0, microsecond=0) # Start from the next hour
    
    # Pass representative coordinates
    lat, lon = example_lat, example_lon

    params = {
        "lat": lat,
        "lon": lon,
        "altitude": 0 # Assuming ground level, can be adjusted if elevation data is available
    }

    try:
        response = requests.get(MET_API_URL, headers=MET_API_HEADERS, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        
        forecast_data = []
        
        for forecast_point in data['properties']['timeseries']:
            # Ensure timestamp is UTC and timezone-naive for consistency with project requirements
            timestamp_iso = forecast_point['time']
            # Parse with timezone info, then convert to UTC, then make it naive for comparison/storage
            timestamp = datetime.fromisoformat(timestamp_iso).astimezone(datetime.now().astimezone().tzinfo).replace(tzinfo=None)

            if start_forecast <= timestamp < end_forecast:
                current_weather = forecast_point['data']['instant']['details']
                
                temperature = current_weather.get('air_temperature')
                # Wind speed is in 'instant' data, not 'next_1_hours'
                wind_speed = current_weather.get('wind_speed') 
                precipitation = forecast_point['data'].get('next_1_hours', {}).get('precipitation') 

                forecast_data.append({
                    'timestamp': timestamp,
                    'temperature': temperature,
                    'wind_speed': wind_speed,
                    'precipitation': precipitation,
                })
        
        df_forecast = pd.DataFrame(forecast_data)
        
        if not df_forecast.empty:
            df_forecast = df_forecast.set_index('timestamp')
            logging.info(f"Successfully fetched {len(df_forecast)} forecast points from MET API.")
        else:
            logging.warning("No forecast data found within the specified time range from MET API.")
        
        return df_forecast

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching MET Norway forecast: {e}")
        return pd.DataFrame()
    except KeyError as e:
        logging.error(f"Error parsing MET Norway API response: Missing key {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"An unexpected error occurred during MET Norway API fetch: {e}")
        return pd.DataFrame()

# --- Example Usage ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Fetch forecast for the next 48 hours
    now = datetime.utcnow().replace(tzinfo=None)
    start_forecast = now.replace(minute=0, second=0, microsecond=0)
    end_forecast = start_forecast + timedelta(hours=48)

    if start_forecast < now:
        start_forecast = now.replace(minute=0, second=0, microsecond=0)

    forecast_df = fetch_met_forecast(lat=58.1467, lon=7.9956, start_time=start_forecast, end_time=end_forecast) # Pass lat/lon explicitly in example

    if not forecast_df.empty:
        print("MET Norway Forecast Data (first 5 rows):")
        print(forecast_df.head())
        print("
MET Norway Forecast Data (last 5 rows):")
        print(forecast_df.tail())
    else:
        print("Failed to retrieve MET Norway forecast data.")
