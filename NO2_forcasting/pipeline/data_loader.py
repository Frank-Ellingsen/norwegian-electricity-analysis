import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_merge_data() -> pd.DataFrame:
    """
    Loads raw CSVs and merges them into a single hourly DataFrame.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "data")
    
    prices_file = os.path.join(data_path, "prices_no2.csv")
    weather_file = os.path.join(data_path, "weather_no2.csv")
    hydrology_file = os.path.join(data_path, "hydrology_no2.csv")

    # 1. Load Prices (Hourly)
    if not os.path.exists(prices_file):
        logging.error("Prices file missing.")
        return pd.DataFrame()
    
    df = pd.read_csv(prices_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('timestamp')

    # 2. Load and Pivot Weather (Daily)
    if os.path.exists(weather_file):
        weather_df = pd.read_csv(weather_file)
        weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'], utc=True)
        # Pivot so variables are columns
        weather_pivoted = weather_df.pivot_table(
            index='timestamp', 
            columns=['station_id', 'variable'], 
            values='value'
        )
        weather_pivoted.columns = [f"weather_{s}_{v}" for s, v in weather_pivoted.columns]
        weather_pivoted = weather_pivoted.reset_index()
        
        # Join on date part
        df['date'] = df['timestamp'].dt.date
        weather_pivoted['date'] = weather_pivoted['timestamp'].dt.date
        df = df.merge(weather_pivoted.drop(columns='timestamp'), on='date', how='left')
        
        # Forward fill daily data across the 24 hours
        weather_cols = [c for c in df.columns if c.startswith('weather_')]
        df[weather_cols] = df[weather_cols].ffill().bfill()
        df = df.drop(columns='date')

    # 3. Load and Pivot Hydrology (Daily)
    if os.path.exists(hydrology_file):
        hyd_df = pd.read_csv(hydrology_file)
        hyd_df['timestamp'] = pd.to_datetime(hyd_df['timestamp'], utc=True)
        hyd_pivoted = hyd_df.pivot_table(
            index='timestamp',
            columns=['target_name', 'role'],
            values='value'
        )
        hyd_pivoted.columns = [f"hyd_{t}_{r}" for t, r in hyd_pivoted.columns]
        hyd_pivoted = hyd_pivoted.reset_index()
        
        df['date'] = df['timestamp'].dt.date
        hyd_pivoted['date'] = hyd_pivoted['timestamp'].dt.date
        df = df.merge(hyd_pivoted.drop(columns='timestamp'), on='date', how='left')
        
        # Forward fill hydrology across the 24 hours
        hyd_cols = [c for c in df.columns if c.startswith('hyd_')]
        df[hyd_cols] = df[hyd_cols].ffill().bfill()
        df = df.drop(columns='date')

    logging.info(f"Merged data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

if __name__ == "__main__":
    df = load_and_merge_data()
    if not df.empty:
        print(df.head())
