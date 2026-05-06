import pandas as pd
import numpy as np
import logging
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, mean_absolute_percentage_error

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def evaluate_predictions(y_true, y_pred):
    """
    Computes RMSE, MAE, and MAPE.
    """
    rmse = root_mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    
    metrics = {
        "RMSE": rmse,
        "MAE": mae,
        "MAPE": mape
    }
    
    logging.info(f"Evaluation Metrics: {metrics}")
    return metrics

def run_evaluation():
    """
    Evaluates the model on the latest 168 hours (test set).
    """
    import os
    from dataset_split import split_dataset
    from forecast import generate_forecast

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "data", "features_no2.csv")
    
    if not os.path.exists(data_path):
        logging.error("❌ Data file missing for evaluation.")
        return

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    train_df, test_df = split_dataset(df, test_hours=168)
    
    if test_df.empty:
        logging.error("❌ Test set is empty.")
        return

    # Use the train_df's tail to generate a "forecast" for the test period
    # This simulates a real forecasting scenario using only historical data
    y_true = test_df['price']
    
    # Generate recursive forecast starting from the end of training
    # We pass the train_df as the starting point
    y_pred_df = generate_forecast(train_df, horizon_hours=168)
    
    if y_pred_df.empty:
        logging.error("❌ Forecast generation failed.")
        return

    y_pred = y_pred_df['price']
    
    # Ensure they are aligned (though they should be)
    metrics = evaluate_predictions(y_true, y_pred)
    
    # Save metrics to a file
    metrics_path = os.path.join(base_path, "output", "metrics_no2.csv")
    pd.DataFrame([metrics]).to_csv(metrics_path, index=False)
    logging.info(f"✅ Evaluation complete. Metrics saved to {metrics_path}")

if __name__ == "__main__":
    run_evaluation()
