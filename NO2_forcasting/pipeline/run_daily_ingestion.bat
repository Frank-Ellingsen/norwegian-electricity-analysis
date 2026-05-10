@echo off
REM --- Combined script for Windows Task Scheduler ---
REM This batch file runs Python scripts sequentially to ingest data.

REM --- Configuration ---
REM Set the path to your Python executable.
REM If 'python' is in your system's PATH, you can simply use 'SET PYTHON_EXE=python'.
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

REM --- Script 2: NO2 Timeseries Pipeline (TEMPORARILY COMMENTED OUT - USES SQLITE, NEEDS REFACTORING TO CSV) ---
REM echo.
REM echo Running no2_timeseries_pipeline.py...
REM %PYTHON_EXE% "%SCRIPT_DIR%no2_timeseries_pipeline.py"
REM IF %ERRORLEVEL% NEQ 0 (
REM     echo ERROR: no2_timeseries_pipeline.py failed with exit code %ERRORLEVEL%.
REM     REM Optional: uncomment the line below to pause and see errors when running manually
REM     REM pause
REM     REM Optional: uncomment the line below to stop the batch file execution on error
REM     REM exit /b %ERRORLEVEL%
REM ) ELSE (
REM     echo no2_timeseries_pipeline.py completed successfully.
REM )
echo.

echo All enabled scripts finished successfully.
REM Optional: uncomment the line below to pause and see output when running manually
REM pause
