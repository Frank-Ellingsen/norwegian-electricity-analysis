import pandas as pd
import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nordpool_prices(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Placeholder function to simulate fetching Nord Pool hourly prices for NO2 zone.
    Generates dummy data.
    """
    logging.info(f"Simulating fetching Nord Pool prices from {start_date} to {end_date}")
    
    # Generate hourly timestamps
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date) + timedelta(days=1) - timedelta(hours=1) # Ensure end_date is inclusive for full day
    
    time_range = pd.date_range(start=start_datetime, end=end_datetime, freq='H', tz='UTC')
    
    # Generate dummy prices and assign to NO2 zone
    prices = {
        'timestamp': time_range,
        'zone': ['NO2'] * len(time_range),
        'price': [10 + i % 50 + (i % 24) * 0.5 for i in range(len(time_range))] # Simple varying price
    }
    
    df = pd.DataFrame(prices)
    logging.info(f"Generated {len(df)} dummy Nord Pool price entries.")
    return df

def save_nordpool_data(df: pd.DataFrame, output_path: str):
    """
    Overwrites the CSV file with the given DataFrame.
    """
    if df.empty:
        logging.info("No Nord Pool data to save.")
        return

    # Ensure the incoming DataFrame's timestamp is UTC
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(df)} Nord Pool rows to new file {output_path}")

