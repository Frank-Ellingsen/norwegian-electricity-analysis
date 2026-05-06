import os
import requests
import pandas as pd
import logging
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nordpool_prices(target_date: date, zone: str = "NO2") -> pd.DataFrame:
    """
    Retrieves hourly spot prices for a specific zone and date from the utilitarian proxy.
    """
    url = (
        f"https://spot.utilitarian.io/electricity/"
        f"{zone}/{target_date.year}/"
        f"{target_date.month:02d}/"
        f"{target_date.day:02d}/"
    )

    logging.info(f"Fetching Nord Pool prices for {zone} on {target_date}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Filter for full hours only
        filtered_data = [
            {"timestamp": entry["timestamp"], "price": float(entry["value"])}
            for entry in data
            if ":00:" in entry["timestamp"]
        ]

        df = pd.DataFrame(filtered_data)
        if not df.empty:
            df.loc[:, 'timestamp'] = pd.to_datetime(df['timestamp'])
            df.loc[:, 'zone'] = zone
            
        return df

    except Exception as e:
        logging.error(f"Error fetching Nord Pool prices: {e}")
        return pd.DataFrame()

def save_nordpool_data(df: pd.DataFrame, output_path: str):
    """
    Appends data to a CSV file, ensuring no duplicates and consistent column names.
    """
    if df.empty:
        return

    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        existing_df.loc[:, 'timestamp'] = pd.to_datetime(existing_df['timestamp'])
        
        # Consolidate 'prices' and 'price' if both exist
        if 'prices' in existing_df.columns:
            if 'price' not in existing_df.columns:
                existing_df = existing_df.rename(columns={'prices': 'price'})
            else:
                existing_df.loc[:, 'price'] = existing_df['price'].fillna(existing_df['prices'])
                existing_df = existing_df.drop(columns='prices')

        # Combine and drop duplicates
        combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['timestamp', 'zone'], keep='last')
        combined_df.to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    logging.info(f"Saved {len(df)} Nord Pool rows to {output_path}")

if __name__ == "__main__":
    yesterday = date.today() - timedelta(days=1)
    prices_df = fetch_nordpool_prices(yesterday)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(base_path, "data", "prices_no2.csv")
    
    if not prices_df.empty:
        save_nordpool_data(prices_df, output_file)
