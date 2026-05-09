import logging
from datetime import date, timedelta
from api.nordpool_api import fetch_nordpool_prices, save_nordpool_data
from api.met_api import fetch_met_observations, save_met_data
from api.nve_api import fetch_hydapi_data, save_hydapi_data
from pipeline.data_loader import load_and_merge_data
from pipeline.feature_engineering import create_features
import os
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_ingestion(start_date: date, end_date: date):
    """
    Runs all API ingestion modules for the specified date range.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "..", "data") # Adjusted path to 'data' folder
    os.makedirs(data_path, exist_ok=True)

    # 1. Nord Pool
    prices_df = fetch_nordpool_prices(start_date, end_date)
    save_nordpool_data(prices_df, os.path.join(data_path, "prices_no2.csv"))

    # 2. MET (Weather)
    weather_df = fetch_met_observations(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    save_met_data(weather_df, os.path.join(data_path, "weather_no2.csv"))

    # 3. NVE (Hydrology)
    hyd_df = fetch_hydapi_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    save_hydapi_data(hyd_df, os.path.join(data_path, "hydrology_no2.csv"))

from pipeline.model_train import train_model
from pipeline.evaluate import evaluate_forecast
from pipeline.forecast import generate_forecast

def main():
    logging.info("🚀 Starting full NO2 Forecasting Pipeline")
    
    # Define forecast parameters
    forecast_start_date = date(2026, 5, 1)
    forecast_horizon_days = 7
    
    # Define historical data range for training
    history_end_date = forecast_start_date - timedelta(days=1)
    # Fetch at least a year of data to generate all features (especially lag_168)
    history_start_date = history_end_date - timedelta(days=90) # Reduced history to 90 days

    logging.info(f"Ingesting data from {history_start_date} to {history_end_date}")
    
    # Step 1: Ingest data
    run_ingestion(history_start_date, history_end_date)
    
    # --- DEBUG START ---
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "..", "data")
    prices_file = os.path.join(data_path, "prices_no2.csv")
    
    logging.info(f"DEBUG: Inspecting prices_no2.csv at: {prices_file}")
    try:
        debug_prices_df = pd.read_csv(prices_file)
        debug_prices_df['timestamp'] = pd.to_datetime(debug_prices_df['timestamp'], utc=True)
        logging.info(f"DEBUG: prices_no2.csv shape: {debug_prices_df.shape}")
        logging.info(f"DEBUG: prices_no2.csv head:\n{debug_prices_df.head()}")
        logging.info(f"DEBUG: prices_no2.csv tail:\n{debug_prices_df.tail()}")
    except Exception as e:
        logging.error(f"DEBUG: Error reading prices_no2.csv: {e}")
    # --- DEBUG END ---
    
    # Step 2: Load & Merge ingested data
    df = load_and_merge_data()
    
    if not df.empty:
        # Step 3: Feature Engineering
        df_features = create_features(df)
        
        # Save processed features
        base_path = os.path.dirname(os.path.abspath(__file__))
        features_path = os.path.join(base_path, "..", "data", "features_no2.csv") # Adjusted path
        df_features.to_csv(features_path)
        logging.info(f"✅ Features saved to {features_path}")

        # Step 4: Training 
        logging.info("🧠 Training model...")
        # Use data up to history_end_date for training
        train_df = df_features[df_features.index.date <= history_end_date]
        if train_df.empty:
            logging.error("❌ Training DataFrame is empty. Cannot train model.")
            return

        model = train_model(train_df)

        # Step 5: Generate Forecast
        logging.info(f"🔮 Generating {forecast_horizon_days}-day forecast from {forecast_start_date}...")
        
        # Pass the last part of the training data to the forecast function
        # This will be used to generate lags for the first forecast steps
        forecast_input_df = df_features[df_features.index.date <= history_end_date].copy()
        
        forecast_output_df = generate_forecast(
            forecast_input_df, 
            horizon_hours=forecast_horizon_days * 24
        )

        if not forecast_output_df.empty:
            # Step 6: Combine Actuals and Forecasts for Visualization
            # Extract actual prices for the forecast period from the full df_features
            actuals_for_forecast_period = df_features[
                (df_features.index.date >= forecast_start_date) & 
                (df_features.index.date < forecast_start_date + timedelta(days=forecast_horizon_days))
            ][['price']]
            actuals_for_forecast_period = actuals_for_forecast_period.rename(columns={'price': 'actual_price'})

            # Merge actuals and forecasts
            combined_forecast_output = forecast_output_df[['price']].rename(columns={'price': 'predicted_price'})
            combined_forecast_output = combined_forecast_output.merge(
                actuals_for_forecast_period, 
                left_index=True, 
                right_index=True, 
                how='left'
            )
            combined_forecast_output.index.name = 'timestamp'
            
            forecast_output_path = os.path.join(base_path, "..", "output", "forecast_vs_actuals_no2.csv")
            combined_forecast_output.to_csv(forecast_output_path)
            logging.info(f"✨ Forecast (with actuals) saved to {forecast_output_path}")

            # Optional: Run evaluation on the generated forecast against actuals (if actuals are available)
            if not actuals_for_forecast_period.empty:
                logging.info("📊 Evaluating generated forecast...")
                # Align dataframes for evaluation by matching timestamps
                eval_df = combined_forecast_output.dropna(subset=['actual_price', 'predicted_price'])
                if not eval_df.empty:
                    evaluate_predictions(eval_df['actual_price'], eval_df['predicted_price'])
                else:
                    logging.warning("No overlapping actuals and predictions for evaluation.")
            else:
                logging.warning("No actual prices available for the forecast period to run evaluation.")

        else:
            logging.error("❌ Forecast generation failed.")

        logging.info("🎯 Full pipeline run complete.")
    else:
        logging.error("❌ Pipeline failed: No data merged.")

if __name__ == "__main__":
    main()
