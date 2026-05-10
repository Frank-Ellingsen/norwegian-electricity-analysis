import os
import pandas as pd
import numpy as np # Added numpy import
import logging
from catboost import CatBoostRegressor
from datetime import datetime, timedelta, date

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_forecast(df_historical_features: pd.DataFrame, zone_to_forecast: str, horizon_hours: int = 24, target_col: str = 'price', model=None):
    """
    Generates a recursive multi-step forecast for a specific NO2 bidding zone.
    
    Args:
        df_historical_features (pd.DataFrame): DataFrame containing historical features and target.
                                                Must be sorted by timestamp and indexed by timestamp.
        zone_to_forecast (str): The specific zone to forecast (e.g., 'NO2').
        horizon_hours (int): The number of hours into the future to forecast.
        target_col (str): The name of the target column (e.g., 'price').
        model: The trained CatBoost model to use for forecasting. If None, it will attempt to load it.

    Returns:
        pd.DataFrame: A DataFrame containing the generated forecasts, indexed by timestamp.
                      Columns include 'predicted_price'.
    """
    logging.info(f"🚀 Generating {horizon_hours}-hour recursive forecast for zone: {zone_to_forecast}")

    # Ensure df_historical_features is indexed by timestamp and sorted
    if not isinstance(df_historical_features.index, pd.DatetimeIndex):
        logging.error("❌ df_historical_features must have a DatetimeIndex.")
        return pd.DataFrame()
    df_historical_features = df_historical_features.sort_index()

    # Filter data for the specific zone
    df_zone = df_historical_features[df_historical_features['zone'] == zone_to_forecast].copy()
    if df_zone.empty:
        logging.error(f"❌ No data available for zone: {zone_to_forecast}. Cannot generate forecast.")
        return pd.DataFrame()

    # Load model if not provided
    if model is None:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_path, "models", f"catboost_{zone_to_forecast}.cbm")

        if not os.path.exists(model_path):
            logging.error(f"❌ Model file not found at {model_path} for zone {zone_to_forecast}. Please train the model for this zone first.")
            return pd.DataFrame()

        model = CatBoostRegressor()
        model.load_model(model_path)

    # We take the latest available data as the starting point
    # Ensure we have enough history for the longest lag (168h)
    if len(df_zone) < 168:
        logging.error(f"❌ Not enough historical data for zone {zone_to_forecast} to generate lags (need at least 168 hours).")
        return pd.DataFrame()

    # The dataframe for iterative predictions will initially be our historical data
    current_forecast_df = df_zone.copy()
    
    # Get the last timestamp from the historical data
    last_historical_ts = current_forecast_df.index[-1]

    predictions_list = []
    
    # Pre-fetch weather forecasts for the entire horizon once before the loop (Kristiansand as NO2 representative)
    NO2_LAT = 58.1467
    NO2_LON = 7.9956
    
    # Define fetch window for weather: from the next hour after last_historical_ts until end of forecast horizon
    # Ensure weather forecasts cover the entire horizon. Fetch a bit extra for safety.
    weather_fetch_start_time = last_historical_ts + timedelta(hours=1)
    weather_fetch_end_time = weather_fetch_start_time + timedelta(hours=horizon_hours + 24) # Fetch a bit extra
    
    # Import inside function to avoid circular dependency if met_api also imports forecast
    from api.met_api import fetch_met_forecast 
    all_future_weather_forecast = fetch_met_forecast(NO2_LAT, NO2_LON, weather_fetch_start_time, weather_fetch_end_time)
    
    if all_future_weather_forecast.empty:
        logging.warning("⚠️ No future weather forecasts available. Exogenous weather features will be NaN.")

    for i in range(horizon_hours):
        current_ts = last_historical_ts + timedelta(hours=i+1)

        # 1. Initialize new_row_data for the current timestamp
        new_row_data = {}

        # Add Time Features
        new_row_data['hour'] = current_ts.hour
        new_row_data['weekday'] = current_ts.weekday()
        new_row_data['month'] = current_ts.month
        new_row_data['is_weekend'] = 1 if current_ts.weekday() >= 5 else 0

        # Add Exogenous Features (Weather)
        # Try to get weather for current_ts from pre-fetched forecast
        if not all_future_weather_forecast.empty and current_ts in all_future_weather_forecast.index:
            weather_features_for_current_ts = all_future_weather_forecast.loc[current_ts]
            new_row_data['temperature'] = weather_features_for_current_ts.get('temperature', np.nan) # Changed pd.NA to np.nan
            new_row_data['wind_speed'] = weather_features_for_current_ts.get('wind_speed', np.nan) # Changed pd.NA to np.nan
            new_row_data['precipitation'] = weather_features_for_current_ts.get('precipitation', np.nan) # Changed pd.NA to np.nan
        else:
            logging.warning(f"Weather forecast not available for {current_ts}. Falling back to NaN for weather features.")
            new_row_data['temperature'] = np.nan # Changed pd.NA to np.nan
            new_row_data['wind_speed'] = np.nan # Changed pd.NA to np.nan
            new_row_data['precipitation'] = np.nan # Changed pd.NA to np.nan

        # Add 'zone' column to new_row_data
        new_row_data['zone'] = zone_to_forecast

        # Convert new_row_data to a Series, aligning its index with `current_forecast_df` columns for consistency
        # Ensure that new_row has all expected feature columns, filling missing with NA
        new_row_series = pd.Series(new_row_data, name=current_ts)
        
        # Create a temporary single-row DataFrame for feature engineering
        temp_df_for_features = pd.DataFrame([new_row_series])
        temp_df_for_features.index = pd.DatetimeIndex([current_ts])
        temp_df_for_features = temp_df_for_features.reindex(columns=df_historical_features.columns, fill_value=np.nan) # Changed pd.NA to np.nan

        # Re-apply feature engineering for lags and rolling means
        # This requires the history of `current_forecast_df`
        
        # Calculate lags based on current_forecast_df
        temp_df_for_features[f'lag_1'] = current_forecast_df[target_col].iloc[-1] if not current_forecast_df.empty else np.nan # Changed pd.NA to np.nan
        
        lag_24_ts = current_ts - timedelta(hours=24)
        lag_168_ts = current_ts - timedelta(hours=168)
        
        temp_df_for_features[f'lag_24'] = current_forecast_df.loc[lag_24_ts, target_col] if lag_24_ts in current_forecast_df.index else np.nan # Changed pd.NA to np.nan
        temp_df_for_features[f'lag_168'] = current_forecast_df.loc[lag_168_ts, target_col] if lag_168_ts in current_forecast_df.index else np.nan # Changed pd.NA to np.nan

        # Calculate rolling features based on current_forecast_df
        if len(current_forecast_df) >= 24:
            temp_df_for_features[f'roll_mean_24'] = current_forecast_df[target_col].tail(24).mean()
            temp_df_for_features[f'roll_std_24'] = current_forecast_df[target_col].tail(24).std()
        else:
            temp_df_for_features[f'roll_mean_24'] = np.nan # Changed pd.NA to np.nan
            temp_df_for_features[f'roll_std_24'] = np.nan # Changed pd.NA to np.nan

        # Drop the zone column from X_predict as it's not a model feature
        X_predict = temp_df_for_features.drop(columns=[target_col, 'zone'], errors='ignore')
        
        # Ensure categorical features are treated as such
        cat_features = ['hour', 'weekday', 'month', 'is_weekend']
        for col in cat_features:
            if col in X_predict.columns:
                X_predict[col] = X_predict[col].astype(int)

        # Realign columns with the model's expected features
        model_features = model.feature_names_
        # Add missing columns (if any) with 0 or a suitable default
        missing_cols = set(model_features) - set(X_predict.columns)
        for c in missing_cols:
            X_predict[c] = 0 
        # Ensure order matches training
        X_predict = X_predict[model_features] 

        try:
            pred = model.predict(X_predict)[0]
        except Exception as e:
            logging.error(f"Error predicting for {current_ts} in zone {zone_to_forecast}: {e}")
            pred = np.nan # Changed pd.NA to np.nan

        # Store the prediction
        new_row_predicted = temp_df_for_features.copy() # Make a copy to avoid SettingWithCopyWarning
        new_row_predicted.loc[current_ts, target_col] = pred
        predictions_list.append(new_row_predicted)
        
        # Append the new prediction to current_forecast_df for subsequent lag/rolling calculations
        current_forecast_df = pd.concat([current_forecast_df, new_row_predicted])

    # Combine all predictions
    if predictions_list:
        combined_forecast_df = pd.concat(predictions_list)
        
        # Ensure the 'price' column contains the predictions.
        # It should already be there from `new_row_predicted.loc[current_ts, target_col] = pred`.
        
        # Filter for the forecast period (future timestamps)
        predictions_for_evaluation = combined_forecast_df[combined_forecast_df.index > last_historical_ts]
        
        # Ensure the 'price' column exists in the returned DataFrame for evaluation.
        # It should be present from `new_row_predicted.loc[current_ts, target_col] = pred`.
        if target_col not in predictions_for_evaluation.columns:
            logging.error(f"Critical error: '{target_col}' column not found in predictions for {zone_to_forecast}.")
            return pd.DataFrame() # Return empty if critical column is missing

        logging.info(f"✅ Forecast generated for zone {zone_to_forecast}. Horizon: {horizon_hours} hours.")
        return predictions_for_evaluation # Return DataFrame with 'price' column containing predictions.

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

            # Load the pre-trained model for NO2 for demonstration
            model_path = os.path.join(base_path, "models", "catboost_no2.cbm")
            if not os.path.exists(model_path):
                logging.error(f"Model not found at {model_path}. Please run model_train.py first to train the model.")
                exit()
            
            trained_model = CatBoostRegressor()
            trained_model.load_model(model_path)

            for zone in unique_zones:
                forecast_for_zone = generate_forecast(df_features, zone_to_forecast=zone, horizon_hours=24, model=trained_model)
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
