import pandas as pd
import os
import logging
import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_merge_data(base_data_dir: str) -> pd.DataFrame:
    """
    Loads raw CSVs and merges them into a single hourly DataFrame.
    """
    all_dfs = []

    # 1. Load Prices (Hourly) from ingested_prices directory
    ingested_prices_dir = os.path.join(base_data_dir, "ingested_prices")
    
    if not os.path.exists(ingested_prices_dir):
        logging.error(f"Ingested prices directory missing: {ingested_prices_dir}")
        return pd.DataFrame()

    price_files = glob.glob(os.path.join(ingested_prices_dir, "*_electricity_prices.csv"))
    if not price_files:
        logging.warning(f"No electricity price files found in {ingested_prices_dir}")
        return pd.DataFrame()

    for price_file in sorted(price_files): # Process in chronological order
        try:
            df_price = pd.read_csv(price_file)
            # Consolidate column names if necessary
            if 'prices' in df_price.columns and 'price' not in df_price.columns:
                df_price = df_price.rename(columns={'prices': 'price'})
            elif 'prices' in df_price.columns and 'price' in df_price.columns:
                df_price['price'] = df_price['price'].fillna(df_price['prices'])
                df_price = df_price.drop(columns='prices')
            all_dfs.append(df_price)
            logging.info(f"Loaded {os.path.basename(price_file)}")
        except Exception as e:
            logging.error(f"Error loading price file {price_file}: {e}")
            continue
            
    if not all_dfs:
        logging.error("No price data successfully loaded.")
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values(['timestamp', 'zone']).drop_duplicates(subset=['timestamp', 'zone']) # Handle potential duplicates from multiple files
    # Removed pivot and stack operations to keep zone as a separate column

    logging.info(f"All prices loaded. Total records: {len(df)}. Timestamp dtype: {df['timestamp'].dtype}")
    
    # 2. Load Weather (Commented out until data source is refactored to CSV)
    # weather_file = os.path.join(base_data_dir, "weather_no2.csv")
    # if os.path.exists(weather_file):
    #     df_weather = pd.read_csv(weather_file)
    #     df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp'], utc=True)
    #     df_weather = df_weather.set_index('timestamp')
    #     df = pd.merge(df, df_weather, left_on='timestamp', right_index=True, how='left') # Merge on timestamp, assuming weather is not zone-specific
    #     logging.info(f"Weather data loaded. Shape: {df_weather.shape}")
    # else:
    #     logging.warning(f"Weather file not found: {weather_file}")

    # 3. Load Hydrology (Commented out until data source is refactored to CSV)
    # hydrology_file = os.path.join(base_data_dir, "hydrology_no2.csv")
    # if os.path.exists(hydrology_file):
    #     df_hydrology = pd.read_csv(hydrology_file)
    #     df_hydrology['timestamp'] = pd.to_datetime(df_hydrology['timestamp'], utc=True)
    #     df_hydrology = df_hydrology.set_index('timestamp')
    #     df = pd.merge(df, df_hydrology, left_on='timestamp', right_index=True, how='left') # Merge on timestamp, assuming hydrology is not zone-specific
    #     logging.info(f"Hydrology data loaded. Shape: {df_hydrology.shape}")
    # else:
    #     logging.warning(f"Hydrology file not found: {hydrology_file}")

    logging.info(f"DEBUG(data_loader): final df shape: {df.shape}")
    logging.info(f"DEBUG(data_loader): final df head:\n{df.head()}")
    logging.info(f"DEBUG(data_loader): final df tail:\n{df.tail()}")

    return df

if __name__ == "__main__":
    # Assuming data directory is relative to the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    data_dir_for_test = os.path.join(project_root, "data")
    
    logging.info(f"Attempting to load data from: {data_dir_for_test}")
    df = load_and_merge_data(data_dir_for_test)
    if not df.empty:
        logging.info("Data loaded successfully:")
        logging.info(df.head())
    else:
        logging.warning("No data loaded.")
