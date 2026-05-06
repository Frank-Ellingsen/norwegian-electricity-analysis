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

if __name__ == "__main__":
    pass
