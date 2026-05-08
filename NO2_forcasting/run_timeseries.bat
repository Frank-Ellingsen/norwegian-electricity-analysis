@echo on

cd /d "C:\Users\Lenovo\OneDrive\Desktop\datafrank\norwegian-electricity-analysis\NO2_forcasting"

"C:\Users\Lenovo\miniconda3\envs\no2_forecasting\python.exe" "pipeline\no2_timeseries_pipeline.py" >> output.log 2>&1

pause