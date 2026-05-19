import logging
import sqlite3
import pandas as pd
from pathlib import Path

class Tools:
    def load_csv(self, path: str) -> pd.DataFrame:
        logging.info("Loading CSV: %s", path)
        return pd.read_csv(path)

    def save_csv(self, df: pd.DataFrame, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        logging.info("Saving CSV: %s", path)
        df.to_csv(path, index=False)

    def connect_sqlite(self, path: str) -> sqlite3.Connection:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        logging.info("Connecting SQLite: %s", path)
        return sqlite3.connect(path)
