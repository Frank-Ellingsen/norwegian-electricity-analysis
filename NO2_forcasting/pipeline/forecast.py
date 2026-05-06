import os
import pandas as pd
import logging
from catboost import CatBoostRegressor
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_forecast(df: pd.DataFrame, horizon_hours: int = 24, target_col: str = 'price'):
    """
    Generates a recursive multi-step forecast for the NO2 bidding zone.
    """
    logging.info(f"🚀 Generating {horizon_hours}-hour recursive forecast.")

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_path, "models", "catboost_no2.cbm")

    if not os.path.exists(model_path):
        logging.error(f"❌ Model file not found at {model_path}. Please train the model first.")
        return pd.DataFrame()

    model = CatBoostRegressor()
    model.load_model(model_path)

    # We take the latest available data as the starting point
    # Ensure we have enough history for the longest lag (168h)
    forecast_df = df.copy().sort_index()
    if len(forecast_df) < 168:
        logging.error("❌ Not enough historical data to generate lags (need at least 168 hours).")
        return pd.DataFrame()

    # Get the last timestamp
    last_ts = forecast_df.index[-1]

    # We will append predictions one by one
    for i in range(horizon_hours):
        current_ts = last_ts + timedelta(hours=i+1)

        # 1. Prepare features for the current timestamp
        # We need to compute lags based on the latest available data (which includes previous predictions)
        new_row = pd.DataFrame(index=[current_ts])

        # Exogenous drivers: In a real scenario, these would come from MET/ENTSO-E forecasts.
        # Here, we carry forward the last known values as a baseline or assume they exist in the DF if provided.
        # For this implementation, we'll ffill exogenous columns from the previous row.
        for col in forecast_df.columns:
            if col != target_col:
                new_row[col] = forecast_df[col].iloc[-1]

        # 2. Update Time Features
        new_row['hour'] = current_ts.hour
        new_row['weekday'] = current_ts.weekday
        new_row['month'] = current_ts.month
        new_row['is_weekend'] = 1 if current_ts.weekday() >= 5 else 0

        # 3. Update Lags (Critical for recursive)
        new_row['lag_1'] = forecast_df[target_col].iloc[-1]

        # For lag_24 and lag_168, we look back from the new timestamp
        target_24 = current_ts - timedelta(hours=24)
        target_168 = current_ts - timedelta(hours=168)

        if target_24 in forecast_df.index:
            new_row['lag_24'] = forecast_df.loc[target_24, target_col]
        if target_168 in forecast_df.index:
            new_row['lag_168'] = forecast_df.loc[target_168, target_col]

        # 4. Update Rolling Mean (Simple 24h window)
        new_row['roll_mean_24'] = forecast_df[target_col].tail(24).mean()
        new_row['roll_std_24'] = forecast_df[target_col].tail(24).std()

        # 5. Predict
        X = new_row.drop(columns=[target_col], errors='ignore')
        # Ensure cat_features match training
        cat_features = ['hour', 'weekday', 'month', 'is_weekend']
        for col in cat_features:
            X[col] = X[col].astype(int)

        pred = model.predict(X)[0]
        new_row[target_col] = pred

        # Append to the dataframe
        forecast_df = pd.concat([forecast_df, new_row])

    # Extract only the forecast period
    result = forecast_df.tail(horizon_hours)
    logging.info(f"✅ Forecast generated. Horizon: {horizon_hours} hours.")
    return result

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "data", "features_no2.csv")

    if os.path.exists(data_path):
        df = pd.read_csv(data_path, index_col=0, parse_dates=True)
        forecast = generate_forecast(df, horizon_hours=24)
        if not forecast.empty:
            output_path = os.path.join(base_path, "output", "predictions_no2.csv")
            forecast.to_csv(output_path)
            print(forecast[['price']].head())
    else:
        logging.error("Features file not found. Run run_pipeline.py first.")

if __name__ == "__main__":
    pass
