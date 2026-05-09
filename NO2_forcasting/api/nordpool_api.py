def save_nordpool_data(df: pd.DataFrame, output_path: str):
    """
    Overwrites the CSV file with the given DataFrame.
    """
    if df.empty:
        logging.info("No Nord Pool data to save.")
        return

    # Ensure the incoming DataFrame's timestamp is UTC
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(df)} Nord Pool rows to new file {output_path}")
