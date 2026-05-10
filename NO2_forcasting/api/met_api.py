import requests
import pandas as pd
import logging
from datetime import datetime, date, timedelta

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
                wind_speed = current_weather.get('wind_speed') 
                precipitation = forecast_point['data'].get('next_1_hours', {}).get('precipitation_amount') 

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

def fetch_met_observations(start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """
    Placeholder function to simulate fetching historical MET weather observations.
    Generates dummy data based on the date range.
    """
    logging.info(f"Simulating fetching MET observations from {start_date_str} to {end_date_str}")
    
    start_dt = pd.to_datetime(start_date_str).tz_localize('UTC')
    end_dt = pd.to_datetime(end_date_str).tz_localize('UTC') + timedelta(days=1) - timedelta(hours=1)
    
    time_range = pd.date_range(start=start_dt, end=end_dt, freq='H')
    
    data = {
        'timestamp': time_range,
        'temperature': [5 + i % 10 + (i % 24) * 0.1 for i in range(len(time_range))],
        'precipitation': [0.1 * (i % 5) for i in range(len(time_range))],
        'wind_speed': [2 + i % 3 for i in range(len(time_range))]
    }
    
    df = pd.DataFrame(data)
    df = df.set_index('timestamp')
    logging.info(f"Generated {len(df)} dummy MET observation entries.")
    return df

def save_met_data(df: pd.DataFrame, output_path: str):
    """
    Saves the MET weather data DataFrame to a CSV file.
    """
    if df.empty:
        logging.info("No MET weather data to save.")
        return
    df.to_csv(output_path, index=True) # Save index (timestamp)
    logging.info(f"Saved {len(df)} MET weather rows to new file {output_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage for fetch_met_forecast
    now = datetime.utcnow().replace(tzinfo=None)
    start_forecast = now.replace(minute=0, second=0, microsecond=0)
    end_forecast = start_forecast + timedelta(hours=48)

    if start_forecast < now:
        start_forecast = now.replace(minute=0, second=0, microsecond=0)

    forecast_df = fetch_met_forecast(lat=58.1467, lon=7.9956, start_time=start_forecast, end_time=end_forecast)

    if not forecast_df.empty:
        print("MET Norway Forecast Data (first 5 rows):")
        print(forecast_df.head())
        print("MET Norway Forecast Data (last 5 rows):")
        print(forecast_df.tail())
    else:
        print("Failed to retrieve MET Norway forecast data.")

    print("="*30) # Corrected this line to simplify and avoid newline issues

    # Example usage for fetch_met_observations
    today = date.today()
    obs_start_date = today - timedelta(days=7)
    obs_end_date = today - timedelta(days=1)

    observations_df = fetch_met_observations(obs_start_date.strftime("%Y-%m-%d"), obs_end_date.strftime("%Y-%m-%d"))

    if not observations_df.empty:
        print("MET Norway Observations Data (first 5 rows):")
        print(observations_df.head())
        print("MET Norway Observations Data (last 5 rows):")
        print(observations_df.tail())
        # Example of saving observations
        # save_met_data(observations_df, "dummy_met_observations.csv")
    else:
        print("Failed to retrieve MET Norway observations data.")