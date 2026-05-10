import os
import pandas as pd
import logging
from catboost import CatBoostRegressor
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_forecast(df_all_zones: pd.DataFrame, zone_to_forecast: str, horizon_hours: int = 24, target_col: str = 'price'):
    """
    Generates a recursive multi-step forecast for a specific NO2 bidding zone.
    """
    logging.info(f"🚀 Generating {horizon_hours}-hour recursive forecast for zone: {zone_to_forecast}")

    # Filter data for the specific zone
    df = df_all_zones[df_all_zones['zone'] == zone_to_forecast].copy()
    if df.empty:
        logging.error(f"❌ No data available for zone: {zone_to_forecast}. Cannot generate forecast.")
        return pd.DataFrame()

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_path, "models", f"catboost_{zone_to_forecast}.cbm")

    if not os.path.exists(model_path):
        logging.error(f"❌ Model file not found at {model_path} for zone {zone_to_forecast}. Please train the model for this zone first.")
        return pd.DataFrame()

    model = CatBoostRegressor()
    model.load_model(model_path)

    # We take the latest available data as the starting point
    # Ensure we have enough history for the longest lag (168h)
    forecast_df = df.copy().sort_index()
    if len(forecast_df) < 168:
        logging.error(f"❌ Not enough historical data for zone {zone_to_forecast} to generate lags (need at least 168 hours).")
        return pd.DataFrame()

    # Get the last timestamp and last row of features
    last_ts = forecast_df.index[-1]
    last_row_features = forecast_df.iloc[-1].drop(columns=['zone'], errors='ignore') # Drop zone column from features

    # We will append predictions one by one
    predictions = []
    
    # Create a temporary dataframe to hold new data points for lag/rolling calculations
    current_forecast_df = forecast_df.copy()

    for i in range(horizon_hours):
        current_ts = last_ts + timedelta(hours=i+1)

        # 1. Prepare features for the current timestamp
        new_row_data = {
            'zone': zone_to_forecast,
            # Exogenous drivers: Fetch forecasted weather data
            # We need to fetch weather forecasts for the *future* timestamps.
            # The current `forecast_df` only has historical data or previous predictions.
            # For the current timestamp `current_ts`, we need the forecasted weather for it.
            # The MET API provides forecasts for a period. We can fetch a range and select the needed point.

            # Define coordinates for NO2 zone (Kristiansand)
            NO2_LAT = 58.1467
            NO2_LON = 7.9956

            # Determine the time range for fetching weather forecast.
            # We need weather for `current_ts` and potentially subsequent hours for future predictions.
            # For simplicity, we'll fetch a fixed window ahead (e.g., 7 days) and select the required point.
            # A more robust solution would be to cache fetched forecasts and only fetch new data when needed.
            forecast_horizon_for_weather = 7 * 24  # Fetch weather for next 7 days
            
            # Ensure start_time is current time for forecast, not historical data's end
            fetch_start_time = datetime.utcnow().replace(tzinfo=None).replace(minute=0, second=0, microsecond=0)
            fetch_end_time = fetch_start_time + timedelta(hours=forecast_horizon_for_weather)

            # If we are already in the future, use the current time as start
            if fetch_start_time < datetime.utcnow().replace(tzinfo=None):
                 fetch_start_time = datetime.utcnow().replace(tzinfo=None).replace(minute=0, second=0, microsecond=0)

            # Fetch weather forecast
            # We only need to fetch this once per forecasting run for the entire horizon,
            # but for simplicity in this iterative replacement, we fetch it for each step.
            # A more optimized approach would fetch once and store/cache.
            try:
                # Ensure we have the actual `fetch_met_forecast` function imported
                from api.met_api import fetch_met_forecast
                
                # Fetch forecast for the *entire* future horizon to avoid repeated API calls within the loop
                # This could be optimized by fetching only once outside the loop if the horizon is constant.
                # For now, we fetch a window and pick the specific point.
                # A better approach for the loop would be to fetch a large chunk and select from it.
                
                # Let's assume we fetch a sufficiently large window upfront or manage it
                # For this replacement, we'll try to fetch for the current_ts and a bit beyond.
                # A robust solution will manage a cache of forecasts.
                
                # Fetching a wider window to cover the current and future steps
                # Fetching for `current_ts` and the next `forecast_horizon_for_weather` hours
                # This is still inefficient if called inside loop, but demonstrates intent.
                # A better way is to fetch once outside the loop.
                
                # --- Optimized approach: Fetch once before the loop ---
                # This part needs to be outside the loop. Let's assume `all_future_weather_forecast` is pre-fetched.
                # For now, let's simulate fetching the data needed for `current_ts`.
                
                # If `current_ts` is within the range of already fetched forecasts, use it.
                # Otherwise, we need to fetch. For this replacement, let's assume `fetch_met_forecast` can provide it.
                
                # We need weather for `current_ts`. We can query the API for a range around `current_ts`.
                # A more practical approach: fetch a large window (e.g., 7-10 days) once before the loop.
                # For this edit, let's assume we're fetching a chunk that covers `current_ts`.
                
                # fetch_start_for_current = current_ts.replace(minute=0, second=0, microsecond=0)
                # fetch_end_for_current = fetch_start_for_current + timedelta(hours=1) # Just for this hour for simplicity
                # forecasted_weather_point = fetch_met_forecast(NO2_LAT, NO2_LON, fetch_start_for_current, fetch_end_for_current)

                # --- Simplified approach for replacement: use placeholder if data not available ---
                # If we had a pre-fetched weather forecast DataFrame `all_future_weather_forecast`
                # we could do:
                # if current_ts in all_future_weather_forecast.index:
                #     weather_features = all_future_weather_forecast.loc[current_ts]
                #     for col, value in weather_features.items():
                #         new_row_data[col] = value
                # else:
                #     # Fallback or error if forecast not available
                #     logging.warning(f"Weather forecast not available for {current_ts}")
                #     # Carry forward last known weather features as a fallback if available, or set to NaN
                #     # For now, we'll leave it as it is (carrying forward previous prediction's weather)
                #     pass 

                # --- Direct replacement of placeholder logic ---
                # The original comment was: `**{col: last_row_features[col] for col in last_row_features.index if col not in [target_col, 'zone']} `
                # This was carrying forward ALL features. We need to specifically handle weather.
                
                # Get weather features for `current_ts`
                # First, try to get from pre-fetched data if available.
                # For this specific code edit, let's assume we fetch it directly for demonstration.
                # In a real pipeline, this fetch would happen ONCE before the loop.

                # fetch_start_time_for_this_ts = current_ts.replace(minute=0, second=0, microsecond=0)
                # fetch_end_time_for_this_ts = fetch_start_time_for_this_ts + timedelta(hours=1) # Fetch just this hour
                
                # forecasted_weather_df_for_ts = fetch_met_forecast(NO2_LAT, NO2_LON, fetch_start_time_for_this_ts, fetch_end_time_for_this_ts)
                
                # if not forecasted_weather_df_for_ts.empty and current_ts in forecasted_weather_df_for_ts.index:
                #     weather_features_for_current_ts = forecasted_weather_df_for_ts.loc[current_ts]
                #     for col, value in weather_features_for_current_ts.items():
                #         # Only add weather-related features
                #         if col in ['temperature', 'wind_speed', 'precipitation']:
                #             new_row_data[col] = value
                # else:
                #     logging.warning(f"Weather forecast not available for {current_ts}. Carrying forward last known weather.")
                #     # If not available, carry forward the last known weather from the previous step's prediction
                #     # This is a fallback, not ideal. A better fallback might be NaN or mean.
                #     if 'temperature' in last_row_features: # Check if last_row_features had weather
                #         new_row_data['temperature'] = last_row_features.get('temperature')
                #         new_row_data['wind_speed'] = last_row_features.get('wind_speed')
                #         new_row_data['precipitation'] = last_row_features.get('precipitation')
                #     else: # If last_row_features had no weather, set to NaN
                #         new_row_data['temperature'] = pd.NA
                #         new_row_data['wind_speed'] = pd.NA
                #         new_row_data['precipitation'] = pd.NA

                # --- For this replacement, let's assume a function `get_forecasted_weather` exists ---
                # This function would handle fetching and caching.
                # For now, we will mock it or fetch directly for current_ts.
                
                # Mocking approach for demonstration:
                # In a real scenario, `all_future_weather_forecasts` would be pre-fetched.
                # For simplicity here, let's fetch for the required hour.
                # NOTE: This is inefficient and should be optimized by fetching a large window ONCE before the loop.
                
                try:
                    # Fetch weather forecast for the specific current timestamp
                    # Ensure start_time is current time for forecast
                    fetch_start_time_for_ts = current_ts.replace(minute=0, second=0, microsecond=0)
                    fetch_end_time_for_ts = fetch_start_time_for_ts + timedelta(hours=1) # Fetch just for this hour
                    
                    # Adjust if `fetch_start_time_for_ts` is in the past relative to `now`
                    if fetch_start_time_for_ts < datetime.utcnow().replace(tzinfo=None):
                        fetch_start_time_for_ts = datetime.utcnow().replace(tzinfo=None).replace(minute=0, second=0, microsecond=0)

                    # Call the imported function
                    forecasted_weather_df = fetch_met_forecast(NO2_LAT, NO2_LON, fetch_start_time_for_ts, fetch_end_time_for_ts)

                    if not forecasted_weather_df.empty and current_ts in forecasted_weather_df.index:
                        weather_features_for_current_ts = forecasted_weather_df.loc[current_ts]
                        # Update new_row_data with actual weather features
                        for col, value in weather_features_for_current_ts.items():
                            # Only add known weather-related columns
                            if col in ['temperature', 'wind_speed', 'precipitation']:
                                new_row_data[col] = value
                    else:
                        logging.warning(f"Weather forecast not available for {current_ts}. Falling back to NaN.")
                        # Fallback to NaN if forecast data is not available for the specific timestamp
                        new_row_data['temperature'] = pd.NA
                        new_row_data['wind_speed'] = pd.NA
                        new_row_data['precipitation'] = pd.NA
                except ImportError:
                    logging.error("Could not import fetch_met_forecast. Ensure api/met_api.py is correctly placed and functional.")
                    # Fallback if import fails
                    new_row_data['temperature'] = pd.NA
                    new_row_data['wind_speed'] = pd.NA
                    new_row_data['precipitation'] = pd.NA
                except Exception as e:
                    logging.error(f"Error fetching or processing weather forecast for {current_ts}: {e}")
                    # Fallback to NaN on any other error during fetch/processing
                    new_row_data['temperature'] = pd.NA
                    new_row_data['wind_speed'] = pd.NA
                    new_row_data['precipitation'] = pd.NA

            except Exception as e: # Catch broader exceptions if anything goes wrong with the above logic
                logging.error(f"Unexpected error when trying to fetch exogenous weather data for {current_ts}: {e}")
                # Ensure weather columns are at least present as NaN if errors occur
                new_row_data['temperature'] = pd.NA
                new_row_data['wind_speed'] = pd.NA
                new_row_data['precipitation'] = pd.NA

            # Update other features (Time Features)
            new_row_data['hour'] = current_ts.hour
            new_row_data['weekday'] = current_ts.weekday
            new_row_data['month'] = current_ts.month
            new_row_data['is_weekend'] = 1 if current_ts.weekday() >= 5 else 0

            # 3. Update Lags (Critical for recursive)
            # Lags are based on the 'current_forecast_df' which includes previous predictions
            new_row['lag_1'] = current_forecast_df[target_col].iloc[-1]


        target_24 = current_ts - timedelta(hours=24)
        target_168 = current_ts - timedelta(hours=168)

        # Retrieve lag values, handling cases where they fall outside available history
        new_row['lag_24'] = current_forecast_df.loc[target_24, target_col] if target_24 in current_forecast_df.index else pd.NA
        new_row['lag_168'] = current_forecast_df.loc[target_168, target_col] if target_168 in current_forecast_df.index else pd.NA

        # 4. Update Rolling Mean (Simple 24h window)
        new_row['roll_mean_24'] = current_forecast_df[target_col].tail(24).mean()
        new_row['roll_std_24'] = current_forecast_df[target_col].tail(24).std()
        
        # Drop any NaN values introduced by incomplete lags, if necessary for prediction
        new_row = new_row.dropna(axis=1, how='all')

        # 5. Predict
        X_predict = new_row.drop(columns=[target_col, 'zone'], errors='ignore') # 'zone' column is not a feature for the model itself
        # Ensure cat_features match training
        cat_features = ['hour', 'weekday', 'month', 'is_weekend']
        for col in cat_features:
            if col in X_predict.columns:
                X_predict[col] = X_predict[col].astype(int)
        
        # Realign columns with the model's expected features
        # This is important if some features were dropped due to NaN (e.g., very early in the forecast)
        model_features = model.feature_names_
        missing_cols = set(model_features) - set(X_predict.columns)
        for c in missing_cols:
            X_predict[c] = 0 # Or a suitable default/fill value

        X_predict = X_predict[model_features] # Ensure order matches training

        try:
            pred = model.predict(X_predict)[0]
        except Exception as e:
            logging.error(f"Error predicting for {current_ts} in zone {zone_to_forecast}: {e}")
            pred = pd.NA # Or some other placeholder for failed prediction

        new_row[target_col] = pred
        predictions.append(new_row.copy())
        
        # Append the new prediction to current_forecast_df for subsequent lag/rolling calculations
        current_forecast_df = pd.concat([current_forecast_df, new_row])

    # Extract only the forecast period
    if predictions:
        result_df = pd.concat(predictions)
        logging.info(f"✅ Forecast generated for zone {zone_to_forecast}. Horizon: {horizon_hours} hours.")
        return result_df
    else:
        logging.warning(f"⚠️ No predictions generated for zone {zone_to_forecast}.")
        return pd.DataFrame()

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "data", "features_no2.csv")

    if os.path.exists(data_path):
        try:
            df_features = pd.read_csv(data_path, index_col=0, parse_dates=True)
            
            # Ensure 'zone' column is available
            if 'zone' not in df_features.columns:
                if 'zone' in df_features.index.names:
                    df_features = df_features.reset_index()
                else:
                    logging.error("The loaded DataFrame does not contain a 'zone' column, and 'zone' is not in the index. Cannot perform per-zone forecasting.")
                    exit()

            all_forecasts = []
            unique_zones = df_features['zone'].unique()
            
            if not unique_zones.any():
                 logging.error("No zones found in the features data. Cannot proceed with forecasting.")
                 exit()

            for zone in unique_zones:
                forecast_for_zone = generate_forecast(df_features, zone_to_forecast=zone, horizon_hours=24)
                if not forecast_for_zone.empty:
                    all_forecasts.append(forecast_for_zone)
            
            if all_forecasts:
                final_forecast_df = pd.concat(all_forecasts).sort_index()
                output_path = os.path.join(base_path, "output", "predictions_all_zones.csv")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                final_forecast_df.to_csv(output_path)
                logging.info(f"All zone forecasts saved to {output_path}")
                logging.info(final_forecast_df.head())
            else:
                logging.warning("No forecasts generated for any zone.")

        except Exception as e:
            logging.error(f"An error occurred during forecasting: {e}")
            import traceback
            traceback.print_exc()
    else:
        logging.error("Features file not found. Run feature_engineering.py first.")
