import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_features(df: pd.DataFrame, target_column: str = 'price') -> pd.DataFrame:
    """
    Creates lag, rolling, and calendar features.
    """
    logging.info("Starting feature engineering.")
    df = df.copy()
    df.loc[:, 'timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.set_index('timestamp').sort_index()

    # 1. Lag Features
    df.loc[:, 'lag_1'] = df[target_column].shift(1)
    df.loc[:, 'lag_24'] = df[target_column].shift(24)
    df.loc[:, 'lag_168'] = df[target_column].shift(168)

    # 2. Rolling Features
    df.loc[:, 'roll_mean_24'] = df[target_column].shift(1).rolling(window=24).mean()
    df.loc[:, 'roll_std_24'] = df[target_column].shift(1).rolling(window=24).std()

    # 3. Calendar Features
    df.loc[:, 'hour'] = df.index.hour
    df.loc[:, 'weekday'] = df.index.weekday
    df.loc[:, 'month'] = df.index.month
    df.loc[:, 'is_weekend'] = df['weekday'].isin([5, 6]).astype(int)

    # Drop NaN
    initial_shape = df.shape
    df = df.dropna()
    logging.info(f"Feature engineering complete. Initial shape: {initial_shape}, Final shape: {df.shape}")
    
    if df.empty:
        logging.warning("Feature engineering resulted in an empty DataFrame. Check if you have enough historical data (at least 168 hours).")
    
    return df

if __name__ == "__main__":
    from data_loader import load_and_merge_data
    df = load_and_merge_data()
    if not df.empty:
        df_features = create_features(df)
        df_features.to_csv("data/features_no2.csv")