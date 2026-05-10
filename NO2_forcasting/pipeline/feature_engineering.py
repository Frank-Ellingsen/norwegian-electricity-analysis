import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_features(df: pd.DataFrame, target_column: str = 'price') -> pd.DataFrame:
    """
    Creates lag, rolling, calendar, and weather features on a per-zone basis.
    The input DataFrame `df` is expected to have 'timestamp', 'zone', and `target_column`.
    It may also contain weather columns like 'temperature', 'wind_speed', 'precipitation'.
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

        # 3. Weather Features (if available)
        # Add temperature, wind_speed, and precipitation as direct features if they exist
        weather_cols = ['temperature', 'wind_speed', 'precipitation']
        for col in weather_cols:
            if col in group.columns:
                # If the column exists, ensure it's included as a feature.
                # No transformation needed here, just carry it over.
                # If the column was entirely NaN, it might be dropped later or handled by the model.
                # For now, we ensure it's part of the DataFrame.
                pass 
            else:
                # Log a warning if a weather column is expected but not found.
                # This might happen if data_loader.py fails to load weather data or if the column name differs.
                logging.warning(f"Weather column '{col}' not found in DataFrame for zone {group['zone'].iloc[0]}.")
                # Optionally, add a column of NaNs if the model expects it.
                # group.loc[:, col] = pd.NA # Uncomment if NaN columns are preferred over missing columns
        
        # 4. Calendar Features (from original index)
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
    
    # Drop NaN values introduced by lag/rolling features or potentially missing weather data at the beginning
    # Only drop if the target column itself is NaN, which indicates insufficient history
    df_transformed = df_transformed.dropna(subset=[target_column])
    
    # Additional check: If weather columns exist but are all NaN for a zone after feature engineering,
    # this might indicate an issue. However, CatBoost can handle NaNs.
    # We will keep the NaN values for weather features if they exist, as they might be learned as a specific condition.
    
    logging.info(f"Feature engineering complete. Initial shape: {initial_shape}, Final shape: {df_transformed.shape}")
    
    if df_transformed.empty:
        logging.warning("Feature engineering resulted in an empty DataFrame. Check if you have enough historical data (at least 168 hours) per zone and if weather data is loaded correctly.")
    
    return df_transformed

if __name__ == "__main__":
    from data_loader import load_and_merge_data
    
    # Assuming data directory is relative to the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Corrected project_root calculation: go up one level from 'pipeline' to reach 'NO2_forcasting'
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir)) 
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