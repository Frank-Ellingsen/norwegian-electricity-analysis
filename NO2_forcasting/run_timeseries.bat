@echo off

REM Go to project root
cd /d "C:\Users\Lenovo\OneDrive\Desktop\datafrank\norwegian-electricity-analysis\NO2_forcasting"

REM Run timeseries pipeline
"C:\Users\Lenovo\miniconda3\envs\no2_forecasting\python.exe" pipeline\no2_timeseries_pipeline.py >> output.log 2>&1