import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def split_dataset(df: pd.DataFrame, test_hours: int = 168):
    """
    Splits the dataset into training and testing sets based on time.
    """
    df = df.sort_index()
    split_idx = len(df) - test_hours
    
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    logging.info(f"Dataset split: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df

if __name__ == "__main__":
    df = pd.read_csv("data/features_no2.csv", index_col=0, parse_dates=True)
    train, test = split_dataset(df)
