import logging
import sqlite3
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

# Define the path to the SQLite database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "..", "data", "sqlite", "forecast_tracking.db")

def initialize_sqlite_tables(db_path: str):
    """
    Initializes the necessary SQLite tables for forecast tracking and evaluation.
    """
    conn = None
    try:
        logging.info(f"Attempting to connect to DB: {db_path}") # Diagnostic log
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create forecast_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecast_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone TEXT NOT NULL,
                origin_timestamp TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                model_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create forecast_predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecast_predictions (
                prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                zone TEXT NOT NULL,
                origin_timestamp TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                lead_hours INTEGER NOT NULL,
                predicted_price REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES forecast_runs (run_id)
            );
        """)

        # Create forecast_evaluation table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecast_evaluation (
                evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone TEXT NOT NULL,
                origin_timestamp TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                lead_hours INTEGER NOT NULL,
                predicted_price REAL NOT NULL,
                actual_price REAL NOT NULL,
                error REAL NOT NULL,
                abs_error REAL NOT NULL,
                evaluation_date TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        logging.info(f"✅ SQLite tables initialized at {db_path}")
        if os.path.exists(db_path): # Check file size after commit
            logging.info(f"DB file size after table commit: {os.path.getsize(db_path)} bytes")
        else:
            logging.info("DB file does not exist after table commit.")
    except sqlite3.Error as e:
        logging.error(f"❌ SQLite initialization error: {e}")
    finally:
        if conn:
            conn.close()

def run_ingestion(start_date: date, end_date: date):
    """
    Runs all API ingestion modules for the specified date range.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "..", "data")
    os.makedirs(data_path, exist_ok=True)

    # Define and create ingestion subdirectories
    ingested_prices_dir = os.path.join(data_path, "ingested_prices")
    ingested_weather_dir = os.path.join(data_path, "ingested_weather")
    ingested_hydapi_dir = os.path.join(data_path, "ingested_hydapi") # Assuming this will be used for NVE

    os.makedirs(ingested_prices_dir, exist_ok=True)
    os.makedirs(ingested_weather_dir, exist_ok=True)
    os.makedirs(ingested_hydapi_dir, exist_ok=True)

    # 1. Nord Pool
    prices_df = fetch_nordpool_prices(start_date, end_date)
    save_nordpool_data(prices_df, os.path.join(ingested_prices_dir, "prices_no2.csv"))

    # 2. MET (Weather)
    weather_df = fetch_met_observations(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    save_met_data(weather_df, os.path.join(ingested_weather_dir, "weather_no2.csv"))

    # 3. NVE (Hydrology)
    hyd_df = fetch_hydapi_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    save_hydapi_data(hyd_df, os.path.join(ingested_hydapi_dir, "hydrology_no2.csv"))

from pipeline.model_train import train_model
from pipeline.evaluate import evaluate_forecast
from pipeline.forecast import generate_forecast

def main():
    logging.info("🚀 Starting full NO2 Forecasting Pipeline")
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True) # Ensure DB directory exists
    initialize_sqlite_tables(SQLITE_DB_PATH) # Initialize tables

    # Define forecast parameters
    forecast_origin_date = date(2026, 5, 1) # Renamed for clarity
    forecast_horizon_hours = 7 * 24 # 7 days horizon in hours
    
    # Define historical data range for training
    history_end_date = forecast_origin_date - timedelta(days=1)
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
        logging.info("DEBUG: prices_no2.csv head:") # Fixed f-string syntax
        logging.info(debug_prices_df.head().to_string()) # Fixed f-string syntax
        logging.info("DEBUG: prices_no2.csv tail:") # Fixed f-string syntax
        logging.info(debug_prices_df.tail().to_string()) # Fixed f-string syntax
    except Exception as e:
        logging.error(f"DEBUG: Error reading prices_no2.csv: {e}")
    # --- DEBUG END ---
    
    # Step 2: Load & Merge ingested data
    df = load_and_merge_data(data_path) # Pass data_path here
    
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
        logging.info(f"🔮 Generating {forecast_horizon_hours / 24}-day forecast from {forecast_origin_date}...")
        
        # Pass the last part of the training data to the forecast function
        # This will be used to generate lags for the first forecast steps
        forecast_input_df = df_features[df_features.index.date <= history_end_date].copy()
        
        forecast_output_df = generate_forecast(
            forecast_input_df, 
            zone_to_forecast='NO2', # Pass the required argument
            horizon_hours=forecast_horizon_hours
        )

        conn = None # Initialize conn to None
        try:
            if not forecast_output_df.empty:
                conn = sqlite3.connect(SQLITE_DB_PATH)
                cursor = conn.cursor()
                current_datetime_utc = pd.Timestamp.now(tz='UTC').isoformat(timespec='seconds')

                # Insert into forecast_runs
                cursor.execute("""
                    INSERT INTO forecast_runs (zone, origin_timestamp, horizon_hours, model_name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, ('NO2', forecast_origin_date.isoformat(), forecast_horizon_hours, 'CatBoostRegressor', current_datetime_utc))
                run_id = cursor.lastrowid
                logging.info(f"✅ Forecast run recorded with run_id: {run_id}")

                # Insert into forecast_predictions
                predictions_to_insert = []
                # Ensure forecast_output_df index is datetime and UTC
                if not pd.api.types.is_datetime64_any_dtype(forecast_output_df.index):
                    forecast_output_df.index = pd.to_datetime(forecast_output_df.index, utc=True)
                elif forecast_output_df.index.tz is None:
                    forecast_output_df.index = forecast_output_df.index.tz_localize('UTC')

                origin_ts_utc = pd.to_datetime(forecast_origin_date).tz_localize('UTC')

                for index, row in forecast_output_df.iterrows():
                    lead_hours = round((index - origin_ts_utc).total_seconds() / 3600)
                    predictions_to_insert.append((
                        run_id,
                        'NO2',
                        forecast_origin_date.isoformat(),
                        index.isoformat(),
                        lead_hours,
                        row['predicted_price'], # Changed from row['price']
                        current_datetime_utc
                    ))
                cursor.executemany("""
                    INSERT INTO forecast_predictions (run_id, zone, origin_timestamp, timestamp, lead_hours, predicted_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, predictions_to_insert)
                conn.commit()
                logging.info(f"✅ {len(predictions_to_insert)} predictions saved to forecast_predictions table.")

                # Step 6: Combine Actuals and Forecasts for Visualization
                actuals_for_forecast_period = df_features[
                    (df_features.index.date >= forecast_origin_date) & 
                    (df_features.index.date < forecast_origin_date + timedelta(days=forecast_horizon_hours // 24))
                ][['price']]
                actuals_for_forecast_period = actuals_for_forecast_period.rename(columns={'price': 'actual_price'})

                combined_forecast_output = forecast_output_df[['predicted_price']]
                combined_forecast_output = combined_forecast_output.merge(
                    actuals_for_forecast_period, 
                    left_index=True, 
                    right_index=True, 
                    how='left'
                )
                combined_forecast_output.index.name = 'timestamp'
                
                forecast_output_path = os.path.join(base_path, "..", "output", "forecast_vs_actuals_no2.csv")
                os.makedirs(os.path.dirname(forecast_output_path), exist_ok=True) # Ensure output directory exists
                combined_forecast_output.to_csv(forecast_output_path)
                logging.info(f"✨ Forecast (with actuals) saved to {forecast_output_path}")

                # Optional: Run evaluation on the generated forecast against actuals (if actuals are available)
                if not actuals_for_forecast_period.empty:
                    logging.info("📊 Evaluating generated forecast...")
                    eval_df = combined_forecast_output.dropna(subset=['actual_price', 'predicted_price']).copy()
                    
                    if not eval_df.empty:
                        # Call evaluate_forecast instead of evaluate_predictions
                        metrics = evaluate_forecast(eval_df['actual_price'], eval_df['predicted_price'])
                        logging.info(f"Evaluation Metrics: MAE={metrics['MAE']:.2f}, RMSE={metrics['RMSE']:.2f}, MAPE={metrics['MAPE']:.2f}")

                        # Prepare data for forecast_evaluation table
                        evaluation_to_insert = []
                        if not pd.api.types.is_datetime64_any_dtype(eval_df.index):
                            eval_df.index = pd.to_datetime(eval_df.index, utc=True)
                        elif eval_df.index.tz is None:
                            eval_df.index = eval_df.index.tz_localize('UTC')

                        for index, row in eval_df.iterrows():
                            error = row['predicted_price'] - row['actual_price']
                            abs_error = abs(error)
                            lead_hours = round((index - origin_ts_utc).total_seconds() / 3600)
                            evaluation_to_insert.append((
                                'NO2',
                                forecast_origin_date.isoformat(),
                                index.isoformat(),
                                lead_hours,
                                row['predicted_price'],
                                row['actual_price'],
                                error,
                                abs_error,
                                current_datetime_utc
                            ))
                        cursor.executemany("""
                            INSERT INTO forecast_evaluation (zone, origin_timestamp, timestamp, lead_hours, predicted_price, actual_price, error, abs_error, evaluation_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, evaluation_to_insert)
                        conn.commit()
                        logging.info(f"✅ {len(evaluation_to_insert)} evaluation results saved to forecast_evaluation table.")
                    else:
                        logging.warning("No overlapping actuals and predictions for evaluation.")
                else:
                    logging.warning("No actual prices available for the forecast period to run evaluation.")

            else:
                logging.error("❌ Forecast generation failed.")

            logging.info("🎯 Full pipeline run complete.")
        except sqlite3.Error as e:
            logging.error(f"❌ SQLite operation error: {e}")
        finally:
            if conn:
                conn.close()
    else:
        logging.error("❌ Pipeline failed: No data merged.")

if __name__ == "__main__":
    main()

