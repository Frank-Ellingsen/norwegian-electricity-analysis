import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_lag_features(file_path: str, output_file_path: str, target_column: str = 'NO2'):
    """
    Reads an hourly spot price CSV, creates specified lag features, and saves the results to a new CSV.

    Args:
        file_path (str): Path to the input hourly spot price CSV file.
        output_file_path (str): Path where the processed CSV with lag features will be saved.
        target_column (str): The column for which lag features will be created (default: 'NO2').
    """
    logging.info(f"Starting lag feature creation for {file_path}")
    try:
        df = pd.read_csv(file_path)
        logging.info("CSV file loaded successfully.")

        # Convert 'timestamp_utc' to datetime and set as index
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
        df = df.set_index('timestamp_utc')
        df = df.sort_index()
        logging.info("Timestamp column converted and set as index, DataFrame sorted.")

        # Create lag features
        df[f'{target_column}_lag_1'] = df[target_column].shift(1)
        df[f'{target_column}_lag_24'] = df[target_column].shift(24)
        df[f'{target_column}_lag_168'] = df[target_column].shift(168) # 24 * 7 = 168 hours for a week
        logging.info("Lag features (lag_1, lag_24, lag_168) created.")

        # Drop rows with NaN values resulting from lagging
        initial_rows = len(df)
        df.dropna(inplace=True)
        logging.info(f"Dropped {initial_rows - len(df)} rows with NaN values after lagging.")

        # Save the processed DataFrame to a new CSV
        df.to_csv(output_file_path)
        logging.info(f"Processed data with lag features saved to {output_file_path}")

    except FileNotFoundError:
        logging.error(f"Error: Input file not found at {file_path}")
    except KeyError:
        logging.error(f"Error: Required columns ('timestamp_utc' or '{target_column}') not found in the CSV.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Define file paths relative to the project root
    base_path = "C:/Users/Lenovo/OneDrive/Desktop/datafrank/norwegian-electricity-analysis/NO2_forcasting"
    input_csv_path = f"{base_path}/data/NO2_2021_2026_spot_prices_hourly.csv"
    output_csv_path = f"{base_path}/data/NO2_2021_2026_spot_prices_hourly_lagged.csv"

    create_lag_features(input_csv_path, output_csv_path)