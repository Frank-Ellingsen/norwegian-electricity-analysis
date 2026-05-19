import sqlite3
import os
from datetime import datetime

DATABASE_DIR = "data/sqlite"
DATABASE_NAME = os.path.join(DATABASE_DIR, "norway_electricity.db")

def setup_database():
    """
    Sets up the SQLite database and creates necessary tables if they don't exist.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create electricity_prices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS electricity_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_start TEXT NOT NULL,
            time_end TEXT NOT NULL,
            price_nok_per_kwh REAL,
            price_eur_per_kwh REAL,
            price_area TEXT NOT NULL,
            date_retrieved TEXT NOT NULL,
            UNIQUE(time_start, price_area)
        );
    """)

    # Create weather_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            air_temperature REAL,
            precipitation_amount REAL,
            wind_speed REAL,
            weather_symbol_code TEXT,
            date_retrieved TEXT NOT NULL,
            UNIQUE(time, latitude, longitude)
        );
    """)

    # Create reservoir_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservoir_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            area TEXT NOT NULL,
            reservoir_gwh REAL,
            filling_level_percent REAL,
            date_retrieved TEXT NOT NULL,
            UNIQUE(date, area)
        );
    """)

    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' and tables set up successfully.")

if __name__ == "__main__":
    setup_database()
