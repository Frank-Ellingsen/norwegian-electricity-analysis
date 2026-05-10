import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_features(df: pd.DataFrame, target_column: str = 'price') -> pd.DataFrame:
    """
    Creates lag, rolling, and calendar features on a per-zone basis.
    The input DataFrame `df` is expected to have 'timestamp', 'zone', and `target_column`.
    """
    logging.info("Starting feature engineering.")
    df = df.copy()
    
    # Ensure timestamp is datetime and set it as index for easier manipulation
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.set_index('timestamp').sort_index()

    # Apply feature engineering per zone
    def generate_features_for_group(group):
        group = group.copy()
        
        # 1. Lag Features
        group.loc[:, 'lag_1'] = group[target_column].shift(1)
        group.loc[:, 'lag_24'] = group[target_column].shift(24)
        group.loc[:, 'lag_168'] = group[target_column].shift(168)

        # 2. Rolling Features
        # Ensure rolling window is applied to shifted data to prevent data leakage
        group.loc[:, 'roll_mean_24'] = group[target_column].shift(1).rolling(window=24).mean()
        group.loc[:, 'roll_std_24'] = group[target_column].shift(1).rolling(window=24).std()
        
        # 3. Calendar Features (from original index)
        group.loc[:, 'hour'] = group.index.hour
        group.loc[:, 'weekday'] = group.index.weekday
        group.loc[:, 'month'] = group.index.month
        group.loc[:, 'is_weekend'] = group['weekday'].isin([5, 6]).astype(int)
        
        return group

    # Group by zone and apply feature generation
    initial_shape = df.shape
    df_features_list = []
    for zone, group in df.groupby('zone'):
        logging.info(f"Generating features for zone: {zone}")
        featured_group = generate_features_for_group(group)
        df_features_list.append(featured_group)
    
    df_transformed = pd.concat(df_features_list).sort_index()
    
    # Drop NaN values introduced by lag/rolling features
    df_transformed = df_transformed.dropna()
    
    logging.info(f"Feature engineering complete. Initial shape: {initial_shape}, Final shape: {df_transformed.shape}")
    
    if df_transformed.empty:
        logging.warning("Feature engineering resulted in an empty DataFrame. Check if you have enough historical data (at least 168 hours) per zone.")
    
    return df_transformed

if __name__ == "__main__":
    from data_loader import load_and_merge_data
    
    # Assuming data directory is relative to the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    data_dir_for_test = os.path.join(project_root, "data")

    logging.info(f"Attempting to load data from: {data_dir_for_test}")
    df_raw = load_and_merge_data(data_dir_for_test)
    
    if not df_raw.empty:
        df_features = create_features(df_raw, target_column='price')
        
        output_path = os.path.join(project_root, "data", "features_no2.csv")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_features.to_csv(output_path)
        logging.info(f"Features saved to {output_path}")
        logging.info(df_features.head())
    else:
        logging.warning("No raw data loaded for feature engineering.")