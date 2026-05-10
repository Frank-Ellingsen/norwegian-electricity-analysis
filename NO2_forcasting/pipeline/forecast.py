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
            # Exogenous drivers: carry forward last known values (PLACEHOLDER)
            **{col: last_row_features[col] for col in last_row_features.index if col not in [target_col, 'zone']}
        }
        new_row = pd.DataFrame([new_row_data], index=[current_ts])

        # 2. Update Time Features
        new_row['hour'] = current_ts.hour
        new_row['weekday'] = current_ts.weekday
        new_row['month'] = current_ts.month
        new_row['is_weekend'] = 1 if current_ts.weekday() >= 5 else 0

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
