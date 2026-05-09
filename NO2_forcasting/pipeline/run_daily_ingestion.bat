@echo off
REM --- Combined script for Windows Task Scheduler ---
REM This batch file runs two Python scripts sequentially to ingest data.

REM --- Configuration ---
REM Set the path to your Python executable.
REM If 'python' is in your system's PATH, you can simply use 'SET PYTHON_EXE=python'.
REM Example: SET PYTHON_EXE="C:\Users\Lenovo\.pyenv\pyenv-win\versions\3.11.7\python.exe"
SET PYTHON_EXE="C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe"

REM Define the directory where the scripts are located.
SET SCRIPT_DIR=%~dp0

REM --- Script 1: Daily Hourly No Prices to DB ---
echo.
echo Running daily_hourly_no_prices_to_db.py...
%PYTHON_EXE% "%SCRIPT_DIR%daily_hourly_no_prices_to_db.py"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: daily_hourly_no_prices_to_db.py failed with exit code %ERRORLEVEL%.
    REM Optional: uncomment the line below to pause and see errors when running manually
    REM pause
    REM Optional: uncomment the line below to stop the batch file execution on error
    REM exit /b %ERRORLEVEL%
) ELSE (
    echo daily_hourly_no_prices_to_db.py completed successfully.
)

REM --- Script 2: NO2 Timeseries Pipeline ---
echo.
echo Running no2_timeseries_pipeline.py...
%PYTHON_EXE% "%SCRIPT_DIR%no2_timeseries_pipeline.py"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: no2_timeseries_pipeline.py failed with exit code %ERRORLEVEL%.
    REM Optional: uncomment the line below to pause and see errors when running manually
    REM pause
    REM Optional: uncomment the line below to stop the batch file execution on error
    REM exit /b %ERRORLEVEL%
) ELSE (
    echo no2_timeseries_pipeline.py completed successfully.
)
echo.

echo All scripts finished successfully.
REM Optional: uncomment the line below to pause and see output when running manually
REM pause
