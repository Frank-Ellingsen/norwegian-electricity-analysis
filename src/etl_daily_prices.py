"""
ETL module for daily electricity prices.

This module demonstrates the expected structure, coding standards,
and logging patterns for all ETL components in the project.

Steps:
1. Load hourly price CSV from /data/raw
2. Clean column names
3. Convert timestamps to datetime
4. Aggregate to daily average price
5. Save processed dataset to /data/processed
"""

import logging
from pathlib import Path
import pandas as pd


def load_hourly_prices(path: str) -> pd.DataFrame:
    """
    Load hourly electricity prices from a CSV file.

    Parameters
    ----------
    path : str
        Path to the raw hourly CSV file.

    Returns
    -------
    pd.DataFrame
        Raw hourly price data.
    """
    logging.info("Loading hourly price data from %s", path)
    return pd.read_csv(path)


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to lowercase snake_case.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with cleaned column names.
    """
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    logging.info("Cleaned column names: %s", list(df.columns))
    return df


def convert_timestamp(df: pd.DataFrame, column: str = "timestamp") -> pd.DataFrame:
    """
    Convert timestamp column to datetime.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    column : str
        Name of the timestamp column.

    Returns
    -------
    pd.DataFrame
        DataFrame with parsed datetime column.
    """
    df = df.copy()
    df[column] = pd.to_datetime(df[column], errors="coerce")
    logging.info("Converted timestamp column to datetime")
    return df


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate hourly prices to daily average prices.

    Parameters
    ----------
    df : pd.DataFrame
        Hourly price data with a datetime column named 'timestamp'.

    Returns
    -------
    pd.DataFrame
        Daily aggregated price data.
    """
    df = df.copy()
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date", as_index=False)["price"].mean()
    daily.rename(columns={"price": "daily_avg_price"}, inplace=True)
    logging.info("Aggregated hourly data to daily averages")
    return daily


def save_daily(df: pd.DataFrame, path: str) -> None:
    """
    Save daily aggregated data to CSV.

    Parameters
    ----------
    df : pd.DataFrame
        Daily aggregated price data.
    path : str
        Output CSV path.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logging.info("Saved daily dataset to %s", path)


def run_etl(raw_path: str, output_path: str) -> None:
    """
    Full ETL pipeline for daily electricity prices.

    Parameters
    ----------
    raw_path : str
        Path to raw hourly CSV.
    output_path : str
        Path to save processed daily CSV.
    """
    logging.info("Starting ETL pipeline for daily prices")

    df = load_hourly_prices(raw_path)
    df = clean_columns(df)
    df = convert_timestamp(df, column="timestamp")
    daily = aggregate_daily(df)
    save_daily(daily, output_path)

    logging.info("ETL pipeline completed successfully")
