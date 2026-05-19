import requests
import sqlite3
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_DIR = "data/sqlite"
DATABASE_NAME = os.path.join(DATABASE_DIR, "norway_electricity.db")

PRICE_AREAS = ["NO1", "NO2", "NO3", "NO4", "NO5"]

def fetch_and_store_electricity_prices(start_date: datetime, end_date: datetime):
    """
    Fetches electricity prices from hvakosterstrommen.no for a specified date range
    and stores them in the SQLite database.
    """
    logging.info(f"Starting to fetch electricity prices from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    records_inserted = 0
    records_skipped = 0

    delta = end_date - start_date
    for i in range(delta.days + 1):
        target_date = start_date + timedelta(days=i)
        date_str_url = target_date.strftime("%Y/%m-%d") # Format for URL (YYYY/MM-DD)
        
        for area in PRICE_AREAS:
            url = f"https://www.hvakosterstrommen.no/api/v1/prices/{date_str_url}_{area}.json"
            headers = {"User-Agent": "NorwegianElectricityAnalysis/1.0 (frank.developer@example.com)"}
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                time.sleep(1) # Be polite to the API server
                prices_data = response.json()

                for entry in prices_data:
                    time_start = datetime.fromisoformat(entry['time_start']).strftime("%Y-%m-%d %H:%M:%S")
                    time_end = datetime.fromisoformat(entry['time_end']).strftime("%Y-%m-%d %H:%M:%S")
                    price_nok_per_kwh = entry['NOK_per_kWh']
                    price_eur_per_kwh = entry['EUR_per_kWh']
                    date_retrieved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    try:
                        cursor.execute("""
                            INSERT INTO electricity_prices (time_start, time_end, price_nok_per_kwh, 
                                                            price_eur_per_kwh, price_area, date_retrieved)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (time_start, time_end, price_nok_per_kwh, 
                                price_eur_per_kwh, area, date_retrieved))
                        records_inserted += 1
                    except sqlite3.IntegrityError:
                        records_skipped += 1
                        logging.debug(f"Skipping duplicate electricity price entry for {time_start} in {area}")
                    except Exception as e:
                        logging.error(f"Error inserting electricity price data for {time_start} in {area}: {e}")
                
                conn.commit()

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch data for {date_str_url} in {area}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while processing data for {date_str_url} in {area}: {e}")

    conn.close()
    logging.info(f"Finished fetching electricity prices. Inserted: {records_inserted}, Skipped (duplicates): {records_skipped}.")

def fetch_and_store_weather_data(latitude=59.91, longitude=10.75): # Coordinates for Oslo
    """
    Fetches weather forecast data from MET Norway's Locationforecast 2.0 API
    and stores it in the SQLite database.
    """
    logging.info(f"Starting to fetch weather data for lat={latitude}, lon={longitude}.")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    records_inserted = 0
    records_skipped = 0

    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
    headers = {"User-Agent": "NorwegianElectricityAnalysis/1.0 (frank.developer@example.com)"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        weather_data = response.json()

        for timeseries_entry in weather_data['properties']['timeseries']:
            time = timeseries_entry['time']
            details = timeseries_entry['data']['instant']['details']
            next_1_hour = timeseries_entry['data'].get('next_1_hours', {})
            next_6_hours = timeseries_entry['data'].get('next_6_hours', {})
            next_12_hours = timeseries_entry['data'].get('next_12_hours', {})

            air_temperature = details.get('air_temperature')
            wind_speed = details.get('wind_speed')
            precipitation_amount = next_1_hour.get('details', {}).get('precipitation_amount', 0) \
                                   + next_6_hours.get('details', {}).get('precipitation_amount', 0) \
                                   + next_12_hours.get('details', {}).get('precipitation_amount', 0)
            weather_symbol_code = next_1_hour.get('summary', {}).get('symbol_code') or \
                                  next_6_hours.get('summary', {}).get('symbol_code') or \
                                  next_12_hours.get('summary', {}).get('symbol_code')

            date_retrieved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                cursor.execute("""
                    INSERT INTO weather_data (time, latitude, longitude, air_temperature,
                                            precipitation_amount, wind_speed, weather_symbol_code,
                                            date_retrieved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (time, latitude, longitude, air_temperature,
                        precipitation_amount, wind_speed, weather_symbol_code,
                        date_retrieved))
                records_inserted += 1
            except sqlite3.IntegrityError:
                records_skipped += 1
                logging.debug(f"Skipping duplicate weather entry for {time} at lat={latitude}, lon={longitude}")
            except Exception as e:
                logging.error(f"Error inserting weather data for {time}: {e}")

        conn.commit()

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch weather data for lat={latitude}, lon={longitude}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing weather data: {e}")

    conn.close()
    logging.info(f"Finished fetching weather data. Inserted: {records_inserted}, Skipped (duplicates): {records_skipped}.")

def fetch_and_store_reservoir_data(start_date: datetime, end_date: datetime):
    """
    Fetches weekly reservoir statistics from NVE for a specified date range
    and stores them in the SQLite database.
    """
    logging.info(f"Starting to fetch reservoir data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    records_inserted = 0
    records_skipped = 0

    # NVE API for reservoir statistics provides weekly data. We need to iterate by year.
    # The API endpoint format is typically like:
    # https://api.nve.no/magasinstatistikk/api/v1/Magasinstatistikk/Year/{year}
    # However, for historical data for specific areas, it's often aggregated.
    # Let's use a simpler approach first, trying to fetch aggregated data if available
    # or iterate through weeks if a more granular API is found.

    # Based on search results, the NVE Reservoir Statistics API endpoint is:
    # https://api.nve.no/magasinstatistikk/api/v1/Magasinstatistikk/Year/{year}

    # Example: https://api.nve.no/magasinstatistikk/api/v1/Magasinstatistikk/Year/2023

    # The API returns data for the entire year, so we filter by date.
    # The API documentation implies that data might be available for all NO areas and "Whole country"
    
    # We will fetch data for each year in the range
    for year in range(start_date.year, end_date.year + 1):
        url = f"https://api.nve.no/magasinstatistikk/api/v1/Magasinstatistikk/Year/{year}"
        headers = {"User-Agent": "NorwegianElectricityAnalysis/1.0 (frank.developer@example.com)"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            time.sleep(1) # Be polite to the API server
            reservoir_data = response.json()

            # The response structure is an array of objects, where each object represents
            # a week's data for a specific area.
            for entry in reservoir_data:
                # Example entry:
                # {
                #   "aar": 2023,
                #   "uke": 1,
                #   "land": "Hele landet",
                #   "region": "NO1",
                #   "magasinprosent": 80.5,
                #   "magasinvolumGWh": 12345
                # }
                
                # NVE API returns data for 'uke' (week number), not exact date.
                # We need to convert week and year to a date.
                # Assuming the date recorded is the start of the week for simplicity, or end of the week.
                # For consistency with other data, let's aim for a YYYY-MM-DD representation.
                # Let's say it represents the Monday of that week.
                
                year_data = entry.get('aar')
                week_data = entry.get('uke')
                area_data = entry.get('region') # This seems to be the bidding zone (NO1-NO5)
                country_data = entry.get('land') # "Hele landet" for whole country
                reservoir_gwh = entry.get('magasinvolumGWh')
                filling_level_percent = entry.get('magasinprosent')

                # Construct a date from year and week number.
                # Python's isocalendar returns (year, week, weekday). Weekday is 1 for Monday.
                try:
                    # Get the date of the Monday of the given week
                    date_obj = datetime.strptime(f'{year_data}-W{week_data}-1', '%Y-W%W-%w').date()
                except ValueError:
                    # Handle cases where week 53 might not exist in all years for this conversion method
                    # Or other parsing issues. Fallback to start of year.
                    date_obj = datetime(year_data, 1, 1).date()
                
                # Convert to YYYY-MM-DD string
                date_str = date_obj.strftime("%Y-%m-%d")
                
                # Filter by date range
                if start_date.date() <= date_obj <= end_date.date():
                    date_retrieved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    try:
                        # Insert data for specific region (NO1-NO5)
                        if area_data:
                            cursor.execute("""
                                INSERT INTO reservoir_data (date, area, reservoir_gwh, filling_level_percent, date_retrieved)
                                VALUES (?, ?, ?, ?, ?)
                            """, (date_str, area_data, reservoir_gwh, filling_level_percent, date_retrieved))
                            records_inserted += 1
                        
                        # Optionally, insert for "Hele landet" if needed.
                        # For now, let's focus on regions.
                        
                    except sqlite3.IntegrityError:
                        records_skipped += 1
                        logging.debug(f"Skipping duplicate reservoir entry for {date_str} in {area_data}")
                    except Exception as e:
                        logging.error(f"Error inserting reservoir data for {date_str} in {area_data}: {e}")
            
            conn.commit()

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch reservoir data for year {year}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing reservoir data for year {year}: {e}")

    conn.close()
    logging.info(f"Finished fetching reservoir data. Inserted: {records_inserted}, Skipped (duplicates): {records_skipped}.")


if __name__ == "__main__":
    # Ensure the database structure is set up
    from data_setup import setup_database
    setup_database()
    
    # Define date range for historical fetch
    _start_date_historical = datetime(2025, 1, 1)
    _end_date_historical = datetime.now() - timedelta(days=1) # Yesterday

    # Fetch and store historical electricity prices
    # fetch_and_store_electricity_prices(start_date=_start_date_historical, end_date=_end_date_historical)

    # Fetch and store current weather forecast (up to 10 days)
    fetch_and_store_weather_data()

    # Fetch and store historical reservoir data
    # fetch_and_store_reservoir_data(start_date=_start_date_historical, end_date=_end_date_historical)
ata()