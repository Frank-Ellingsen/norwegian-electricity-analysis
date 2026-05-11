import pandas as pd
import numpy as np
import logging
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_mape(y_true: pd.Series, y_pred: pd.Series) -> float:
    """
    Calculates Mean Absolute Percentage Error (MAPE).
    Handles cases where y_true might contain zeros to avoid division by zero.
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    # Filter out elements where y_true is zero to avoid division by zero
    non_zero_mask = y_true != 0
    if not np.any(non_zero_mask):
        return np.inf # Or some other appropriate value if all true values are zero

    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100

def evaluate_forecast(y_true: pd.Series, y_pred: pd.Series) -> dict:
    """
    Evaluates a single forecast against actual values using RMSE, MAE, and MAPE.
    
    Args:
        y_true (pd.Series): Series of actual values.
        y_pred (pd.Series): Series of predicted values.
        
    Returns:
        dict: A dictionary containing 'RMSE', 'MAE', and 'MAPE'.
    """
    if y_true.empty or y_pred.empty or len(y_true) != len(y_pred):
        logging.warning("Cannot evaluate: true or predicted series are empty or have different lengths.")
        return {"RMSE": np.nan, "MAE": np.nan, "MAPE": np.nan}
    
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = calculate_mape(y_true, y_pred) # Using custom MAPE function
    
    return {
        "RMSE": rmse,
        "MAE": mae,
        "MAPE": mape
    }

def evaluate_forecasts(test_dfs: dict, forecast_dfs: dict, target_col: str = 'price') -> pd.DataFrame:
    """
    Computes RMSE, MAE, and MAPE for given true and predicted values for each zone.
    
    Args:
        test_dfs (dict): Dictionary of test DataFrames, keyed by zone.
        forecast_dfs (dict): Dictionary of forecast DataFrames, keyed by zone.
        target_col (str): The name of the target column.
        
    Returns:
        pd.DataFrame: A DataFrame summarizing evaluation metrics for each zone.
    """
    logging.info("Starting forecast evaluation per zone.")
    
    all_metrics = []
    
    for zone, test_df in test_dfs.items():
        if zone not in forecast_dfs:
            logging.warning(f"No forecast found for zone {zone}. Skipping evaluation for this zone.")
            continue
            
        forecast_df = forecast_dfs[zone]

        # Add debugging print statements for timestamp alignment
        logging.info(f"--- Timestamp Debug for Zone: {zone} ---")
        logging.info(f"Test Data Range: {test_df.index.min()} to {test_df.index.max()}")
        logging.info(f"Forecast Data Range: {forecast_df.index.min()} to {forecast_df.index.max()}")
        logging.info(f"--- End Debug ---")

        common_timestamps = test_df.index.intersection(forecast_df.index)

        y_true = test_df.loc[common_timestamps, target_col]
        y_pred = forecast_df.loc[common_timestamps, target_col]

        if y_true.empty or y_pred.empty:
            logging.warning(f"No common timestamps for evaluation in zone {zone}. Skipping.")
            continue

        try:
            metrics = evaluate_forecast(y_true, y_pred)
            all_metrics.append({
                "zone": zone,
                "RMSE": metrics["RMSE"],
                "MAE": metrics["MAE"],
                "MAPE": metrics["MAPE"]
            })
            logging.info(f"Evaluation Metrics for zone {zone}: {metrics}")
        except Exception as e:
            logging.error(f"Error calculating metrics for zone {zone}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not all_metrics:
        logging.warning("No evaluation metrics could be computed for any zone.")
        return pd.DataFrame()

    metrics_df = pd.DataFrame(all_metrics)
    logging.info("Finished forecast evaluation.")
    return metrics_df

if __name__ == "__main__":
    from .data_loader import load_and_merge_data
    from .feature_engineering import create_features
    from .dataset_split import split_dataset
    from .forecast import generate_forecast
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    data_dir_for_test = os.path.join(project_root, "data")
    
    logging.info(f"Running full pipeline for evaluation demonstration from: {data_dir_for_test}")

    try:
        # 1. Load Data
        df_raw = load_and_merge_data(data_dir_for_test)
        if df_raw.empty:
            logging.error("No raw data loaded. Cannot proceed with evaluation.")
            exit()
        
        # 2. Create Features
        df_features = create_features(df_raw, target_column='price')
        if df_features.empty:
            logging.error("No features created. Cannot proceed with evaluation.")
            exit()
        
        # 3. Split Dataset
        # Ensure 'zone' column is available for splitting
        if 'zone' not in df_features.columns:
            if 'zone' in df_features.index.names:
                df_features = df_features.reset_index()
            else:
                logging.error("The loaded DataFrame does not contain a 'zone' column, and 'zone' is not in the index. Cannot perform per-zone split for evaluation.")
                exit()

        splits = split_dataset(df_features, test_hours=24) # Use a smaller test_hours for quick demo
        test_dfs = splits.get('test', {})
        train_dfs = splits.get('train', {}) # Get train data
        
        if not test_dfs:
            logging.error("No test data available for evaluation.")
            exit()

        # 4. Generate Forecasts (requires trained models, assume they exist or create dummy)
        # In a real scenario, you would train models with model_train.py first
        # For demonstration, we'll try to generate forecasts directly.
        
        forecast_dfs = {}
        # Iterate through zones present in the test set to ensure we forecast for relevant zones
        # and use the corresponding training data.
        for zone in test_dfs.keys(): 
            # Get the training data for the current zone
            train_df_for_zone = train_dfs.get(zone)
            if train_df_for_zone is None or train_df_for_zone.empty:
                logging.error(f"No training data available for zone {zone}. Cannot generate forecast.")
                continue
            
            # Pass only training data to generate_forecast so it forecasts for the test period
            forecast_for_zone = generate_forecast(train_df_for_zone, zone_to_forecast=zone, horizon_hours=24)
            if not forecast_for_zone.empty:
                forecast_dfs[zone] = forecast_for_zone
        
        if not forecast_dfs:
            logging.error("No forecasts generated for evaluation. Ensure models are trained and data is available.")
            exit()

        # 5. Evaluate Forecasts
        evaluation_results = evaluate_forecasts(test_dfs, forecast_dfs)
        
        if not evaluation_results.empty:
            output_path = os.path.join(project_root, "output", "evaluation_metrics.csv")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            evaluation_results.to_csv(output_path, index=False)
            logging.info(f"Evaluation metrics saved to {output_path}")
            logging.info("Overall Evaluation Results:")
            logging.info(evaluation_results)
        else:
            logging.warning("No evaluation results to save.")

    except Exception as e:
        logging.error(f"An error occurred during evaluation demonstration: {e}")
        import traceback
        traceback.print_exc()