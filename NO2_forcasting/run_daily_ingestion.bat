@echo off

cd /d "C:\Users\Lenovo\OneDrive\Desktop\datafrank\norwegian-electricity-analysis\NO2_forcasting"

echo Running %DATE% %TIME% >> output.log
"C:\Users\Lenovo\miniconda3\envs\no2_forecasting\python.exe"
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python311\python.exe" 
"C:\Users\Lenovo\OneDrive\Desktop\datafrank\norwegian-electricity-analysis\NO2_forcasting\pipeline\daily_hourly_no_prices_to_db.py" >> output.log 2>&1

pause