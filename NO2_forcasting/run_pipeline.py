import logging
import sqlite3
from datetime import date, timedelta
import os
import pandas as pd

# Import main functions from pipeline scripts
from pipeline.daily_hourly_no_prices_to_db import main as daily_prices_main
from pipeline.no2_timeseries_pipeline import main as timeseries_pipeline_main
from pipeline.data_loader import load_and_merge_data
from pipeline.feature_engineering import create_features
from pipeline.model_train import train_model
from pipeline.evaluate import evaluate_forecast
from pipeline.forecast import generate_forecast

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the path to the SQLite database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "data", "sqlite", "forecast_tracking.db")

def initialize_sqlite_tables(db_path: str):
    """
    Initializes the necessary SQLite tables for forecast tracking and evaluation.
    """
    conn = None
    try:
        logging.info(f"Attempting to connect to DB: {db_path}")
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
        if os.path.exists(db_path):
            logging.info(f"DB file size after table commit: {os.path.getsize(db_path)} bytes")
        else:
            logging.info("DB file does not exist after table commit.")
    except sqlite3.Error as e:
        logging.error(f"❌ SQLite initialization error: {e}")
    finally:
        if conn:
            conn.close()

def run_ingestion_pipeline(ingestion_start_date: date, ingestion_end_date: date):
    """
    Runs the daily prices and exogenous data ingestion pipelines for the specified date range.
    """
    logging.info(f"Starting ingestion for range: {ingestion_start_date} to {ingestion_end_date}")

    # Call daily_hourly_no_prices_to_db.main for each day in range
    current_date = ingestion_start_date
    while current_date <= ingestion_end_date:
        logging.info(f"Calling daily_prices_main for {current_date}")
        daily_prices_main(target_date=current_date)
        current_date += timedelta(days=1)
    
    # Call no2_timeseries_pipeline.main for the range
    # Note: no2_timeseries_pipeline is designed for a start/end date range
    logging.info(f"Calling timeseries_pipeline_main for range: {ingestion_start_date} to {ingestion_end_date}")
    timeseries_pipeline_main(start_date=ingestion_start_date.strftime("%Y-%m-%d"), 
                             end_date=ingestion_end_date.strftime("%Y-%m-%d"))

def main():
    logging.info("🚀 Starting full NO2 Forecasting Pipeline")
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    initialize_sqlite_tables(SQLITE_DB_PATH)

    # --- Dynamic Date Setup ---
    today = date.today()
    # history_end_date will be yesterday for daily run
    history_end_date = today - timedelta(days=1)
    # Fetch at least 168 hours (7 days) for lags, ideally more for model training stability
    # Using 90 days for example, adjust as needed
    history_start_date = history_end_date - timedelta(days=90)
    
    # forecast_origin_date is the day AFTER the last historical data
    forecast_origin_date = history_end_date + timedelta(days=1)
    forecast_horizon_hours = 7 * 24 # 7 days horizon in hours (adjust as needed, e.g., 30*24)

    logging.info(f"Data ingestion range: {history_start_date} to {history_end_date}")
    logging.info(f"Forecast origin date: {forecast_origin_date}")
    logging.info(f"Forecast horizon: {forecast_horizon_hours} hours")
    
    # Step 1: Ingest data using the refactored pipeline scripts
    run_ingestion_pipeline(history_start_date, history_end_date)
    
    # Step 2: Load & Merge ingested data
    # Pass project root for data_loader
    data_path = os.path.join(BASE_DIR, "data")
    df = load_and_merge_data(data_path)
    
    if not df.empty:
        # Step 3: Feature Engineering
        df_features = create_features(df)
        
        # Save processed features
        features_path = os.path.join(BASE_DIR, "data", "features_no2.csv")
        df_features.to_csv(features_path)
        logging.info(f"✅ Features saved to {features_path}")

        # Step 4: Training 
        logging.info("🧠 Training model...")
        # Use data up to history_end_date for training
        train_df = df_features[df_features.index.date <= history_end_date].copy()
        if train_df.empty:
            logging.error("❌ Training DataFrame is empty. Cannot train model.")
            return

        model = train_model(train_df)

        # Step 5: Generate Forecast
        logging.info(f"🔮 Generating {forecast_horizon_hours / 24}-day forecast from {forecast_origin_date}...")
        
        # Pass the last part of the training data to the forecast function
        forecast_input_df = df_features[df_features.index.date <= history_end_date].copy()
        
        forecast_output_df = generate_forecast(
            forecast_input_df, 
            zone_to_forecast='NO2',
            horizon_hours=forecast_horizon_hours,
            model=model # Pass the trained model
        )

        conn = None
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

                # Rename 'price' column to 'predicted_price' for DB insertion consistency
                if 'price' in forecast_output_df.columns:
                    forecast_output_df = forecast_output_df.rename(columns={'price': 'predicted_price'})

                for index, row in forecast_output_df.iterrows():
                    # Calculate lead_hours based on forecast_origin_date, not actual_date for consistency
                    lead_hours = round((index - origin_ts_utc).total_seconds() / 3600)
                    predictions_to_insert.append((
                        run_id,
                        'NO2',
                        forecast_origin_date.isoformat(),
                        index.isoformat(),
                        lead_hours,
                        row['predicted_price'],
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
                ][['price']].copy() # Added .copy() to avoid SettingWithCopyWarning
                actuals_for_forecast_period = actuals_for_forecast_period.rename(columns={'price': 'actual_price'})

                combined_forecast_output = forecast_output_df[['predicted_price']].merge(
                    actuals_for_forecast_period, 
                    left_index=True, 
                    right_index=True, 
                    how='left'
                )
                combined_forecast_output.index.name = 'timestamp'
                
                forecast_output_path = os.path.join(BASE_DIR, "output", "forecast_vs_actuals_no2.csv")
                os.makedirs(os.path.dirname(forecast_output_path), exist_ok=True)
                combined_forecast_output.to_csv(forecast_output_path)
                logging.info(f"✨ Forecast (with actuals) saved to {forecast_output_path}")

                # Optional: Run evaluation on the generated forecast against actuals (if actuals are available)
                if not actuals_for_forecast_period.empty:
                    logging.info("📊 Evaluating generated forecast...")
                    eval_df = combined_forecast_output.dropna(subset=['actual_price', 'predicted_price']).copy()
                    
                    if not eval_df.empty:
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
                            # Ensure lead_hours calculation is consistent
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
