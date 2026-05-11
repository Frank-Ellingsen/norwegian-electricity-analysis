import os
import pandas as pd
import logging
import sqlite3
import sys # Import sys
from catboost import CatBoostRegressor
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project root to sys.path to handle relative imports within the pipeline
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Database Setup ---
# DB_PATH calculation is now relative to project_root for consistency
DB_PATH = os.path.join(project_root, "data", "sqlite", "forecast_tracking.db")

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create forecast_predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forecast_predictions (
                timestamp TIMESTAMP PRIMARY KEY,
                zone TEXT,
                predicted_price REAL,
                origin_timestamp TIMESTAMP,
                lead_hours INTEGER
            )
        ''')

        # Create forecast_evaluation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forecast_evaluation (
                timestamp TIMESTAMP PRIMARY KEY,
                zone TEXT,
                actual_price REAL,
                predicted_price REAL,
                abs_error REAL,
                error REAL,
                lead_hours INTEGER,
                origin_timestamp TIMESTAMP
            )
        ''')

        conn.commit()
        logging.info("✅ Database initialized. Tables 'forecast_predictions' and 'forecast_evaluation' ensured.")
    except Exception as e:
        logging.error(f"❌ Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def insert_predictions(predictions_df: pd.DataFrame):
    """Inserts forecast predictions into the forecast_predictions table."""
    if predictions_df.empty:
        logging.warning("No predictions to insert.")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        # Ensure 'price' column is renamed to 'predicted_price' and 'timestamp' is set as index for insertion consistency
        predictions_df = predictions_df.rename(columns={'price': 'predicted_price'}).set_index('timestamp')
        
        # Add origin_timestamp and lead_hours if not present (they would be constant for a batch)
        # For now, let's assume they are generated or handled before calling this.
        # For simplicity, let's add dummy values if not present.
        if 'origin_timestamp' not in predictions_df.columns:
            predictions_df['origin_timestamp'] = pd.Timestamp.now(tz='UTC') # Placeholder
        if 'lead_hours' not in predictions_df.columns:
            predictions_df['lead_hours'] = (predictions_df.index - predictions_df['origin_timestamp']).dt.total_seconds() / 3600 # Placeholder

        predictions_df.to_sql('forecast_predictions', conn, if_exists='append', index=True, index_label='timestamp')
        conn.commit()
        logging.info(f"✅ Inserted {len(predictions_df)} predictions into forecast_predictions.")
    except Exception as e:
        logging.error(f"❌ Error inserting predictions: {e}")
    finally:
        if conn:
            conn.close()

def insert_evaluation_metrics(metrics_df: pd.DataFrame):
    """Inserts evaluation metrics into the forecast_evaluation table."""
    if metrics_df.empty:
        logging.warning("No evaluation metrics to insert.")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        metrics_df.to_sql('forecast_evaluation', conn, if_exists='append', index=True, index_label='timestamp')
        conn.commit()
        logging.info(f"✅ Inserted {len(metrics_df)} evaluation metrics into forecast_evaluation.")
    except Exception as e:
        logging.error(f"❌ Error inserting evaluation metrics: {e}")
    finally:
        if conn:
            conn.close()
# --- End Database Setup ---


def train_model(train_df: pd.DataFrame, target_col: str = 'price') -> CatBoostRegressor:
    """
    Trains a CatBoost model using the provided DataFrame.
    Saves the trained model and its feature importance.
    """
    logging.info("Starting model training for a single zone (NO2).")
    
    # Categorical features as defined in GEMINI.md
    cat_features = ['hour', 'weekday', 'month', 'is_weekend']
    
    # Ensure target_col is not in features
    feature_cols = [col for col in train_df.columns if col not in [target_col, 'zone']]
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    
    if X_train.empty or y_train.empty:
        logging.error("❌ Training DataFrame is empty. Cannot train model.")
        return None

    # Ensure categorical features are treated as such
    current_cat_features = [f for f in cat_features if f in X_train.columns]
    for col in current_cat_features:
        # Handle potential SettingWithCopyWarning by using .loc
        if col in X_train.columns:
            X_train.loc[:, col] = X_train[col].astype(int)

    model = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.05,
        depth=6,
        loss_function='RMSE',
        verbose=0, # Set to 0 to avoid verbose output during training
        random_seed=42, # For reproducibility
        early_stopping_rounds=50 # Stop if validation metric doesn't improve for 50 rounds
    )
    
    try:
        # For simplicity, using X_train as eval_set. In production, use a separate validation set.
        model.fit(X_train, y_train, cat_features=current_cat_features, eval_set=(X_train, y_train))
        
        # Save Model
        # Adjusted model_dir path to be relative to project_root for consistency
        model_dir = os.path.join(project_root, "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, f"catboost_no2.cbm") # Specific to NO2
        model.save_model(model_path)
        logging.info(f"✅ Model trained and saved to {model_path}")
        
        # Save Feature Importance
        importance = model.get_feature_importance()
        feature_names = X_train.columns
        importance_df = pd.DataFrame({'feature': feature_names, 'importance': importance}).sort_values(by='importance', ascending=False)
        
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        importance_path = os.path.join(output_dir, f"feature_importance_no2.csv") # Specific to NO2
        importance_df.to_csv(importance_path, index=False)
        logging.info(f"✅ Feature importance saved to {importance_path}")
        
        return model
        
    except Exception as e:
        logging.error(f"❌ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return None

# --- Forecasting and Evaluation ---
# Imports using relative paths now that sys.path is configured
from pipeline.forecast import generate_forecast 
# from pipeline.evaluate import evaluate_forecasts # Not directly used here, metrics calculated in-place

def calculate_mape(y_true: pd.Series, y_pred: pd.Series) -> float:
    """
    Calculates Mean Absolute Percentage Error (MAPE).
    Handles cases where y_true might contain zeros to avoid division by zero.
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero_mask = y_true != 0
    if not np.any(non_zero_mask):
        return np.inf
    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100

# Revised calculate_metrics_for_db to accept zone explicitly and use correct structure for DB insertion
def calculate_metrics_for_db(actual_prices: pd.Series, predicted_prices: pd.Series, lead_hours: int, origin_ts: pd.Timestamp, zone: str) -> pd.DataFrame:
    """
    Calculates and formats metrics for database insertion.
    Returns a DataFrame suitable for 'forecast_evaluation' table.
    """
    if actual_prices.empty or predicted_prices.empty or len(actual_prices) != len(predicted_prices):
        logging.warning("Cannot calculate metrics for DB: Input series are empty or have different lengths.")
        return pd.DataFrame()

    # Ensure series are aligned and have timestamps
    common_ts = actual_prices.index.intersection(predicted_prices.index)
    actual_prices = actual_prices.loc[common_ts]
    predicted_prices = predicted_prices.loc[common_ts]

    if actual_prices.empty:
        logging.warning("No common timestamps to calculate metrics for DB.")
        return pd.DataFrame()
    
    rmse = np.sqrt(mean_squared_error(actual_prices, predicted_prices))
    mae = mean_absolute_error(actual_prices, predicted_prices)
    mape = calculate_mape(actual_prices, predicted_prices)
    
    evaluation_ts = origin_ts # Using origin_ts as a representative timestamp for the evaluation batch.
    if isinstance(actual_prices.index, pd.DatetimeIndex) and not actual_prices.empty:
        evaluation_ts = actual_prices.index.max()

    metrics_df = pd.DataFrame([{
        "timestamp": evaluation_ts,
        "zone": zone, # Use passed zone
        "actual_price": np.nan, # Placeholder for aggregate metrics, as DB table has this column
        "predicted_price": np.nan, # Placeholder for aggregate metrics
        "abs_error": mae,
        "error": rmse, 
        "lead_hours": lead_hours, 
        "origin_timestamp": origin_ts
    }])
    
    return metrics_df


if __name__ == "__main__":
    # base_path calculation remains relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    
    # Add project root to sys.path to handle relative imports like 'from pipeline.forecast import ...'
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    features_data_path = os.path.join(project_root, "data", "features_no2.csv")
    model_file_path = os.path.join(project_root, "models", "catboost_no2.cbm")
    db_path_corrected = os.path.join(project_root, "data", "sqlite", "forecast_tracking.db") # Correct DB path
    
    # Update DB_PATH global variable to the corrected path
    DB_PATH = db_path_corrected
    
    # Initialize database and tables
    init_db()

    # Load features data
    logging.info(f"Loading features data from {features_data_path}")
    if not os.path.exists(features_data_path):
        logging.error(f"Features file not found at {features_data_path}. Run feature_engineering.py and model_train.py (training part) first.")
    else:
        try:
            df_features = pd.read_csv(features_data_path, index_col=0, parse_dates=True)
            
            # Ensure 'zone' column is available
            if 'zone' not in df_features.columns:
                if 'zone' in df_features.index.names:
                    df_features = df_features.reset_index()
                else:
                    logging.error("The loaded DataFrame does not contain a 'zone' column, and 'zone' is not in the index. Cannot perform per-zone forecasting or evaluation.")
                    exit()

            # --- Model Training ---
            # Filter for the zone we are training for (assuming NO2 based on model filename)
            zone_for_training = 'NO2'
            df_train_zone = df_features[df_features['zone'] == zone_for_training].copy()
            
            trained_model = train_model(df_train_zone, target_col='price')
            
            if not trained_model:
                logging.error("Model training failed. Exiting.")
                exit()

            # --- Forecasting ---
            horizon_hours = 24 # Forecast for the next 24 hours
            zone_to_forecast = 'NO2'
            
            logging.info(f"Generating {horizon_hours}-hour forecast for {zone_to_forecast}...")
            
            # We need the full historical features dataframe to correctly generate lags and rolling features for forecasting
            # The 'generate_forecast' function expects the entire historical feature set.
            forecast_df_raw = generate_forecast(df_features, zone_to_forecast=zone_to_forecast, horizon_hours=horizon_hours, model=trained_model)
            
            if forecast_df_raw.empty:
                logging.error("Forecast generation failed. Exiting.")
                exit()
            
            # Prepare predictions for database insertion
            predictions_for_db_insert = forecast_df_raw.copy()
            # Rename 'price' column to 'predicted_price' if it exists, otherwise keep as 'predicted_price' if already named that way.
            if 'price' in predictions_for_db_insert.columns:
                predictions_for_db_insert = predictions_for_db_insert.rename(columns={'price': 'predicted_price'})
            
            # Add metadata
            origin_ts = pd.Timestamp.now(tz='UTC')
            predictions_for_db_insert['origin_timestamp'] = origin_ts
            # Calculate lead hours based on forecast timestamps and origin_ts
            predictions_for_db_insert['lead_hours'] = (predictions_for_db_insert.index - origin_ts).total_seconds() / 3600.0
            predictions_for_db_insert['zone'] = zone_to_forecast

            # Ensure all columns expected by DB are present and correctly named
            # Reset index to make timestamp a column for insertion
            predictions_for_db_insert = predictions_for_db_insert.reset_index()
            # Ensure the index column is named 'timestamp' before selection
            if 'timestamp' not in predictions_for_db_insert.columns and 'index' in predictions_for_db_insert.columns:
                predictions_for_db_insert = predictions_for_db_insert.rename(columns={'index': 'timestamp'})
            # Now select the columns, assuming 'timestamp' is correctly named
            predictions_for_db_insert = predictions_for_db_insert[['timestamp', 'zone', 'predicted_price', 'origin_timestamp', 'lead_hours']]
            
            # Insert predictions
            insert_predictions(predictions_for_db_insert)
            
            # --- Evaluation ---
            logging.info("Starting evaluation...")
            
            # Get actual prices for the forecast period from the features DataFrame
            forecast_timestamps = predictions_for_db_insert['timestamp']
            actual_prices_series = df_features.loc[
                (df_features['zone'] == zone_to_forecast) &
                (df_features.index.isin(forecast_timestamps)),
                'price'
            ].reindex(forecast_timestamps) # Reindex to ensure alignment with forecast timestamps
            
            predicted_prices_series = predictions_for_db_insert.set_index('timestamp')['predicted_price']
            
            # Calculate metrics for DB insertion using the revised function
            if not actual_prices_series.empty and not predicted_prices_series.empty:
                metrics_df = calculate_metrics_for_db( # Using the original function name, but it's defined with zone param
                    actual_prices=actual_prices_series,
                    predicted_prices=predicted_prices_series,
                    lead_hours=horizon_hours, # Assuming a single lead_hours for this batch evaluation
                    origin_ts=origin_ts,
                    zone=zone_to_forecast
                )
                
                if not metrics_df.empty:
                    insert_evaluation_metrics(metrics_df)
                else:
                    logging.warning("Metrics DataFrame is empty, no evaluation metrics to insert.")
            else:
                logging.warning("Could not retrieve sufficient actual prices for evaluation, or no common timestamps found.")

            logging.info("Pipeline completed: Model trained, forecast generated, and results saved to DB.")

        except Exception as e:
            logging.error(f"An error occurred during the main pipeline execution: {e}")
            import traceback
            traceback.print_exc()
