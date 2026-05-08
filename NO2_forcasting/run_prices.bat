@echo off

REM Go to project root
cd /d "C:\Users\Lenovo\OneDrive\Desktop\datafrank\norwegian-electricity-analysis\NO2_forcasting"

REM Run script from pipeline folder
"C:\Users\Lenovo\miniconda3\envs\no2_forecasting\python.exe" pipeline\daily_hourly_no_prices_to_db.py >> output.log 2>&1