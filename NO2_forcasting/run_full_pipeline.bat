@echo off
REM --- Full Pipeline Automation Script for Windows Task Scheduler ---

REM --- Configuration ---
REM Set the path to your Python executable.
REM If 'python' is in your system's PATH, you can simply use 'SET PYTHON_EXE=python'.
SET PYTHON_EXE="C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe"

REM Define the project root directory. This script assumes it's run from the project root.
SET PROJECT_ROOT=%~dp0

REM Define a log file for the entire pipeline run
SET LOG_FILE="%PROJECT_ROOT%pipeline_full_run.log"

REM Ensure logging starts fresh
DEL %LOG_FILE% >NUL 2>NUL

echo Pipeline started at %DATE% %TIME% >> %LOG_FILE%
echo ---------------------------------------------------- >> %LOG_FILE%

REM Change directory to the project root
CD /D "%PROJECT_ROOT%"

REM --- Helper function for robust execution ---
:RUN_PYTHON_SCRIPT
    SET SCRIPT_PATH=%1
    SET SCRIPT_NAME=%2
    echo. >> %LOG_FILE%
    echo Running %SCRIPT_NAME%... >> %LOG_FILE%
    echo Command: %PYTHON_EXE% "%SCRIPT_PATH%" >> %LOG_FILE%
    %PYTHON_EXE% "%SCRIPT_PATH%" >> %LOG_FILE% 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: %SCRIPT_NAME% failed with exit code %ERRORLEVEL%. Check %LOG_FILE% for details. >> %LOG_FILE%
        echo Pipeline aborted. >> %LOG_FILE%
        EXIT /B %ERRORLEVEL%
    ) ELSE (
        echo %SCRIPT_NAME% completed successfully. >> %LOG_FILE%
    )
GOTO :EOF

REM --- Pipeline Steps ---

REM 1. Data Ingestion: Daily Prices
CALL :RUN_PYTHON_SCRIPT "pipeline\daily_hourly_no_prices_to_db.py" "daily_hourly_no_prices_to_db.py"

REM 2. Data Ingestion: Exogenous Data (Weather, Hydrology)
CALL :RUN_PYTHON_SCRIPT "pipeline
o2_timeseries_pipeline.py" "no2_timeseries_pipeline.py"

REM 3. Feature Engineering (Loads raw data, creates features, saves data/features_no2.csv)
CALL :RUN_PYTHON_SCRIPT "pipeline\feature_engineering.py" "feature_engineering.py"

REM 4. Model Training (Loads features, trains, saves model/feature_importance, inserts to DB)
CALL :RUN_PYTHON_SCRIPT "pipeline\model_train.py" "model_train.py"

REM 5. Evaluation (Loads features, generates forecasts, evaluates, saves output/evaluation_metrics.csv)
CALL :RUN_PYTHON_SCRIPT "pipeline\evaluate.py" "evaluate.py"

echo. >> %LOG_FILE%
echo All pipeline scripts completed successfully. >> %LOG_FILE%
echo Pipeline finished at %DATE% %TIME% >> %LOG_FILE%

REM Optional: uncomment the line below to pause and see output when running manually
REM pause
