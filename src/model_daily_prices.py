"""
Modeling module for daily electricity prices.

This module consumes the daily ETL output and applies a baseline forecasting model.

Steps:
1. Load daily average price CSV from /data/processed
2. Split data into training and testing sets
3. Train a baseline forecasting model (Naive: last value)
4. Generate forecasts
5. Evaluate model performance
6. Save forecast results and evaluation metrics
"""

import logging
from pathlib import Path
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_daily_prices(path: str) -> pd.DataFrame:
    """
    Load daily electricity prices from a CSV file.

    Parameters
    ----------
    path : str
        Path to the processed daily CSV file.

    Returns
    -------
    pd.DataFrame
        Daily price data.
    """
    logging.info("Loading daily price data from %s", path)
    df = pd.read_csv(path, parse_dates=['date'])
    df = df.sort_values('date').set_index('date')
    logging.info("Loaded %d daily price records.", len(df))
    return df


def train_naive_model(df: pd.DataFrame) -> np.float64:
    """
    Trains a Naive (last value) forecasting model.
    For a naive model, the "training" involves simply identifying the last known value.

    Parameters
    ----------
    df : pd.DataFrame
        Training DataFrame with 'daily_avg_price' column.

    Returns
    -------
    np.float64
        The last known daily average price from the training data.
    """
    last_value = df['daily_avg_price'].iloc[-1]
    logging.info("Naive model trained. Last known value: %.2f", last_value)
    return last_value


def forecast_naive(last_value: np.float64, steps: int) -> np.ndarray:
    """
    Generates forecasts using the Naive (last value) model.

    Parameters
    ----------
    last_value : np.float64
        The last known value from the training data.
    steps : int
        Number of steps to forecast into the future.

    Returns
    -------
    np.ndarray
        Array of forecasted values.
    """
    forecast = np.full(steps, last_value)
    logging.info("Generated %d naive forecasts.", steps)
    return forecast


def evaluate_model(y_true: pd.Series, y_pred: np.ndarray, model_name: str = "Model") -> dict:
    """
    Evaluates the model performance using RMSE, MAE.

    Parameters
    ----------
    y_true : pd.Series
        Actual values.
    y_pred : np.ndarray
        Predicted values.
    model_name : str
        Name of the model being evaluated.

    Returns
    -------
    dict
        Dictionary containing evaluation metrics.
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    
    # MAPE calculation, handle division by zero
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    mape = mape if np.isfinite(mape) else np.nan # Handle cases where y_true might be zero

    logging.info(
        "Evaluation for %s: RMSE=%.2f, MAE=%.2f, MAPE=%.2f%%", model_name, rmse, mae, mape
    )
    return {"rmse": rmse, "mae": mae, "mape": mape}


def run_modeling_pipeline(processed_data_path: str, forecast_output_path: str, metrics_output_path: str, test_size: float = 0.2) -> None:
    """
    Full modeling pipeline for daily electricity prices using a Naive model.

    Parameters
    ----------
    processed_data_path : str
        Path to the processed daily CSV file (output of ETL).
    forecast_output_path : str
        Path to save the forecast results CSV.
    metrics_output_path : str
        Path to save the evaluation metrics CSV.
    test_size : float, optional
        Proportion of the dataset to include in the test split, by default 0.2
    """
    logging.info("Starting modeling pipeline for daily prices")

    df = load_daily_prices(processed_data_path)

    # Split data
    train_size = int(len(df) * (1 - test_size))
    train_df, test_df = df[0:train_size], df[train_size:len(df)]
    logging.info("Data split into training (%d samples) and testing (%d samples).", len(train_df), len(test_df))

    # Train model
    last_value_train = train_naive_model(train_df)

    # Forecast
    forecast_steps = len(test_df)
    naive_forecast = forecast_naive(last_value_train, forecast_steps)
    
    # Create forecast DataFrame with dates from test set
    forecast_df = pd.DataFrame({
        'date': test_df.index,
        'actual_price': test_df['daily_avg_price'],
        'naive_forecast': naive_forecast
    }).set_index('date')

    # Evaluate
    metrics = evaluate_model(test_df['daily_avg_price'], naive_forecast, "Naive Model")

    # Save forecasts
    Path(forecast_output_path).parent.mkdir(parents=True, exist_ok=True)
    forecast_df.to_csv(forecast_output_path, index=True)
    logging.info("Saved forecast results to %s", forecast_output_path)

    # Save metrics
    Path(metrics_output_path).parent.mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame([metrics], index=['Naive Model'])
    metrics_df.to_csv(metrics_output_path, index=True)
    logging.info("Saved evaluation metrics to %s", metrics_output_path)

    logging.info("Modeling pipeline completed successfully")


if __name__ == "__main__":
    # Example usage:
    # Assuming 'daily_prices.csv' is generated by the ETL in data/processed
    PROCESSED_DATA_PATH = Path("../data/processed/daily_prices.csv")
    FORECAST_OUTPUT_PATH = Path("../data/processed/daily_price_forecasts_naive.csv")
    METRICS_OUTPUT_PATH = Path("../analysis/naive_model_metrics.csv")

    # This part should ideally be called after the ETL script has run and generated its output.
    # For demonstration, we assume processed_data_path exists.
    # You might want to create a dummy CSV for initial testing if the ETL hasn't run yet.
    if not PROCESSED_DATA_PATH.exists():
        logging.warning(
            "Processed data file not found at %s. Please run ETL first or create a dummy file.",
            PROCESSED_DATA_PATH
        )
        # Create a dummy file for testing purposes
        dummy_data = {
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10']),
            'daily_avg_price': [50.0, 52.0, 51.5, 53.0, 54.5, 53.5, 55.0, 56.0, 55.5, 57.0]
        }
        dummy_df = pd.DataFrame(dummy_data)
        PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        dummy_df.to_csv(PROCESSED_DATA_PATH, index=False)
        logging.info("Created dummy processed data file at %s for testing.", PROCESSED_DATA_PATH)

    run_modeling_pipeline(
        processed_data_path=str(PROCESSED_DATA_PATH),
        forecast_output_path=str(FORECAST_OUTPUT_PATH),
        metrics_output_path=str(METRICS_OUTPUT_PATH)
    )
