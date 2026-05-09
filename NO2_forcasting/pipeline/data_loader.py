import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_merge_data(data_dir: str) -> pd.DataFrame:
    """
    Loads raw CSVs and merges them into a single hourly DataFrame.
    """
    prices_file = os.path.join(data_dir, "prices_no2.csv")
    weather_file = os.path.join(data_dir, "weather_no2.csv")
    hydrology_file = os.path.join(data_dir, "hydrology_no2.csv")

    # 1. Load Prices (Hourly)
    if not os.path.exists(prices_file):
        logging.error(f"Prices file missing: {prices_file}")
        return pd.DataFrame()
    
    df = pd.read_csv(prices_file)
    # Consolidate column names if necessary
    if 'prices' in df.columns and 'price' not in df.columns:
        df = df.rename(columns={'prices': 'price'})
    elif 'prices' in df.columns and 'price' in df.columns:
        df['price'] = df['price'].fillna(df['prices'])
        df = df.drop(columns='prices')

    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('timestamp')
    logging.info(f"Prices loaded. Timestamp dtype: {df['timestamp'].dtype}")
    
    # --- DEBUG START ---
    logging.info(f"DEBUG(data_loader): df shape after prices load: {df.shape}")
    logging.info(f"DEBUG(data_loader): df head after prices load:\n{df.head()}")
    logging.info(f"DEBUG(data_loader): df tail after prices load:\n{df.tail()}")
    # --- DEBUG END ---

    return df # Temporarily return only price data

if __name__ == "__main__":
    df = load_and_merge_data()
    if not df.empty:
        print(df.head())
