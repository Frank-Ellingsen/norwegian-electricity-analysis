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
    df = df.set_index('timestamp').sort_index()

    # 1. Lag Features
    df[f'lag_1'] = df[target_column].shift(1)
    df[f'lag_24'] = df[target_column].shift(24)
    df[f'lag_168'] = df[target_column].shift(168)

    # 2. Rolling Features
    df[f'roll_mean_24'] = df[target_column].shift(1).rolling(window=24).mean()
    df[f'roll_std_24'] = df[target_column].shift(1).rolling(window=24).std()

    # 3. Calendar Features
    df['hour'] = df.index.hour
    df['weekday'] = df.index.weekday
    df['month'] = df.index.month
    df['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)

    # Drop NaN
    df = df.dropna()
    logging.info(f"Feature engineering complete. Final shape: {df.shape}")
    return df

if __name__ == "__main__":
    from data_loader import load_and_merge_data
    df = load_and_merge_data()
    if not df.empty:
        df_features = create_features(df)
        df_features.to_csv("data/features_no2.csv")