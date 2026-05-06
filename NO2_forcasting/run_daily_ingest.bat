@echo off
set "PROJECT_DIR=C:\Users\Lenovo\OneDrive\Desktop\datafrank\norwegian-electricity-analysis\NO2_forcasting"
set "PYTHON_EXE=C:\Program Files\Python314\python.exe"
set "SCRIPT_PATH=%PROJECT_DIR%\run_pipeline.py"

echo [%date% %time%] Starting NO2 Modular Pipeline...
cd /d "%PROJECT_DIR%"
"%PYTHON_EXE%" "%SCRIPT_PATH%" >> "%PROJECT_DIR%\ingest_log.txt" 2>&1
echo [%date% %time%] Finished.
