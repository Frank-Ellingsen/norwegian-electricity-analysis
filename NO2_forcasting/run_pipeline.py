import logging
from datetime import date, timedelta
from api.nordpool_api import fetch_nordpool_prices, save_nordpool_data
from api.met_api import fetch_met_observations, save_met_data
from api.nve_api import fetch_hydapi_data, save_hydapi_data
from pipeline.data_loader import load_and_merge_data
from pipeline.feature_engineering import create_features
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_ingestion():
    """
    Runs all API ingestion modules for yesterday's data.
    """
    yesterday = date.today() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "data")
    os.makedirs(data_path, exist_ok=True)

    # 1. Nord Pool
    prices_df = fetch_nordpool_prices(yesterday)
    save_nordpool_data(prices_df, os.path.join(data_path, "prices_no2.csv"))

    # 2. MET (Weather)
    weather_df = fetch_met_observations(yesterday_str, yesterday_str)
    save_met_data(weather_df, os.path.join(data_path, "weather_no2.csv"))

    # 3. NVE (Hydrology)
    hyd_df = fetch_hydapi_data(yesterday_str, yesterday_str)
    save_hydapi_data(hyd_df, os.path.join(data_path, "hydrology_no2.csv"))

def main():
    logging.info("🚀 Starting full NO2 Forecasting Pipeline")
    
    # Step 1: Ingest
    run_ingestion()
    
    # Step 2: Load & Merge
    df = load_and_merge_data()
    
    if not df.empty:
        # Step 3: Feature Engineering
        df_features = create_features(df)
        
        # Save processed features
        base_path = os.path.dirname(os.path.abspath(__file__))
        features_path = os.path.join(base_path, "data", "features_no2.csv")
        df_features.to_csv(features_path)
        logging.info(f"✅ Pipeline run complete. Features saved to {features_path}")
    else:
        logging.error("❌ Pipeline failed: No data merged.")

if __name__ == "__main__":
    main()
