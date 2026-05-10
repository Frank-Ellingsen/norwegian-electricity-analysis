import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def split_dataset(df: pd.DataFrame, test_hours: int = 168):
    """
    Splits the dataset into training and testing sets based on time, per zone.
    
    Args:
        df (pd.DataFrame): The input DataFrame, expected to have 'zone' column and a datetime index.
        test_hours (int): The number of hours to reserve for the test set for each zone.
        
    Returns:
        dict: A dictionary with 'train' and 'test' keys, each containing another dictionary
              where keys are zone names and values are the corresponding DataFrames.
    """
    logging.info(f"Splitting dataset into train and test sets for {test_hours} test hours per zone.")
    
    train_dfs = {}
    test_dfs = {}
    
    if 'zone' not in df.columns:
        logging.warning("No 'zone' column found. Performing a global split.")
        df = df.sort_index()
        split_idx = len(df) - test_hours
        train_dfs['global'] = df.iloc[:split_idx]
        test_dfs['global'] = df.iloc[split_idx:]
    else:
        for zone, group in df.groupby('zone'):
            group = group.sort_index()
            if len(group) < test_hours:
                logging.warning(f"Zone {zone} has less than {test_hours} hours of data. Skipping split for this zone.")
                continue
            
            split_idx = len(group) - test_hours
            train_dfs[zone] = group.iloc[:split_idx]
            test_dfs[zone] = group.iloc[split_idx:]
            logging.info(f"Zone {zone} split: Train={len(train_dfs[zone])}, Test={len(test_dfs[zone])}")

    if not train_dfs and not test_dfs:
        logging.error("No data available for splitting after grouping by zone.")
        return {}, {} # Return empty dictionaries

    return {'train': train_dfs, 'test': test_dfs}

if __name__ == "__main__":
    
    # Assuming data directory is relative to the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    data_path = os.path.join(project_root, "data", "features_no2.csv")
    
    if os.path.exists(data_path):
        logging.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path, index_col=0, parse_dates=True)
        
        # Make sure 'zone' column is correctly identified if not already the case (e.g. from data_loader)
        if 'zone' not in df.columns:
            # If 'zone' is part of the index after loading, reset index to make it a column
            if 'zone' in df.index.names:
                df = df.reset_index()
            else:
                logging.error("The loaded DataFrame does not contain a 'zone' column, and 'zone' is not in the index. Cannot perform per-zone split.")
                exit()
        
        splits = split_dataset(df)
        
        if splits:
            for zone_name, train_df in splits['train'].items():
                logging.info(f"Train data for {zone_name} (first 5 rows):\n{train_df.head()}")
            for zone_name, test_df in splits['test'].items():
                logging.info(f"Test data for {zone_name} (first 5 rows):\n{test_df.head()}")
        else:
            logging.warning("No train/test splits were generated.")
    else:
        logging.error(f"Data file not found at {data_path}. Please run feature_engineering.py first.")
