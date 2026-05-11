# ⚡ NO2 Electricity Price Forecasting System

## Table of Contents
1.  [Overview](#1-overview)
2.  [Objective](#2-objective)
3.  [Data Sources](#3-data-sources)
    *   [Electricity Prices (Target)](#electricity-prices-target)
    *   [Exogenous Variables](#exogenous-variables)
4.  [Feature Engineering](#4-feature-engineering)
    *   [Current Features](#current-features)
    *   [Planned Features](#planned-features)
5.  [Pipeline Architecture](#5-pipeline-architecture)
    *   [Scripts](#scripts)
6.  [Dataset Splitting](#6-dataset-splitting)
7.  [Model Specification](#7-model-specification)
    *   [Model](#model)
    *   [Configuration](#configuration)
    *   [Categorical Features](#categorical-features)
8.  [Forecasting Strategy](#8-forecasting-strategy)
9.  [Storage Architecture](#9-storage-architecture)
10. [Evaluation Strategy](#10-evaluation-strategy)
11. [Execution](#11-execution)
12. [Deployment](#12-deployment)
13. [Advanced System Enhancements (Future Improvements)](#13-advanced-system-enhancements-future-improvements)
14. [Streamlit Dashboard (Live Monitoring)](#14-streamlit-dashboard-live-monitoring)
    *   [Project Structure](#project-structure)
    *   [Installation](#installation)
    *   [Run the Dashboard](#run-the-dashboard)
    *   [Data Sources Used](#data-sources-used)
    *   [Core Dashboard Features](#core-dashboard-features)
    *   [Deployment Options](#deployment-options)
    *   [Best Practices](#best-practices)
    *   [Future Dashboard Enhancements](#future-dashboard-enhancements)
15. [Critical Engineering Notes](#15-critical-engineering-notes)
16. [System Summary](#16-system-summary)
17. [Status](#17-status)

---

## 1. Overview

This project implements a **production-grade time series forecasting system** for **NO2 (Southern Norway) electricity prices** using a **CatBoost regression model**. The system predicts hourly electricity prices, generates rolling multi-step forecasts, and tracks month-ahead accuracy.

**Key capabilities:**
*   Predicts **hourly electricity prices** for the NO2 bidding zone.
*   Uses **recursive multi-step forecasting** to generate a rolling 30-day (720-hour) forecast daily.
*   Tracks true month-ahead forecast accuracy.
*   Stores pipeline outputs primarily in **CSV format**, with forecast predictions and evaluation results tracked in a SQLite database for monitoring.

---

## 2. Objective

The primary objectives of this system are to:
*   Forecast **hourly electricity prices for NO2** with high accuracy.
*   Utilize a rich set of **historical, engineered, and exogenous features**.
*   Recalculate forecasts **daily** using a rolling window approach.
*   Rigorously evaluate **true 30-day-ahead prediction performance**.

---

## 3. Data Sources

### Electricity Prices (Target)

Hourly electricity prices are ingested and stored.
*   **Source:** Utilitarian Spot API (Nord Pool Prices)
*   **Output:** CSV files in `data/ingested_prices/`
*   **Key fields:** `timestamp`, `zone`, `price_eur_per_mwh`

### Exogenous Variables

Exogenous data is ingested from various APIs and stored as CSV files.

*   **Sources:** MET Norway, ENTSO-E, NVE Hydrology
*   **Output:** CSV files in `data/ingested_weather/` and `data/ingested_hydapi/` (though `no2_timeseries_pipeline.py` consolidates these into `ingested_weather`)
*   **Includes:**
    *   **🌡 Weather (MET Norway):** temperature, precipitation
    *   **💧 Hydrology (NVE):** reservoir levels, inflow, snow water equivalent (SWE)
    *   **⚡ Grid (ENTSO-E):** cross-border flows, Net Transfer Capacity (NTC)

---

## 4. Feature Engineering

Features are generated on a per-zone basis to enrich the dataset for the forecasting model.

### Current Features

*   **Time Features:** `hour`, `weekday`, `month`, `is_weekend`
*   **Lag Features:** `lag_1`, `lag_24`, `lag_168` (representing 1 hour, 1 day, and 1 week prior)
*   **Rolling Features:** `roll_mean_24`, `roll_std_24` (24-hour rolling mean and standard deviation of the target)
*   **Weather Features:** `temperature`, `precipitation` (derived from MET Norway data)
*   **Exogenous Features:** `wind_speed`, `flows`, `capacities`, `hydrology` (where available)

### Planned Features

*   Full integration of Hydrology indicators (NVE).
*   Incorporation of forecasted weather inputs (moving away from forward-filling historical data).
*   Inclusion of public holidays and demand proxies.

---

## 5. Pipeline Architecture

The forecasting pipeline is designed for modularity, reproducibility, and CSV-based data handling, with a tracking database for forecasts and evaluations.

```mermaid
graph TD
    subgraph DATA [Data]
        A[External APIs] --> B(Ingestion: Daily Prices<br>(daily_hourly_no_prices_to_db.py));
        A --> C(Ingestion: Exogenous Data<br>(no2_timeseries_pipeline.py));
        B --> D(Data Loading<br>(data_loader.py)<br>Output: /data/features_no2.csv);
        C --> D;
    end

    subgraph MODELING [Modeling]
        D --> E(Feature Engineering<br>(feature_engineering.py));
        E --> F(Dataset Split<br>(dataset_split.py));
        F --> G(Model Training<br>(model_train.py));
        G --> H(Forecasting<br>(forecast.py));
        H --> I(Evaluation<br>(evaluate.py));
    end

    subgraph OUTPUT [Output]
        I --> J(Final Outputs<br>predictions_no2.csv<br>feature_importance.csv<br>evaluation_metrics.csv);
    end
```

### Scripts

*   `pipeline/daily_hourly_no_prices_to_db.py`: Ingests daily hourly electricity prices from the Utilitarian Spot API to CSV.
*   `pipeline/no2_timeseries_pipeline.py`: Ingests daily exogenous data (weather, hydrology) from MET and NVE APIs to CSV.
*   `pipeline/data_loader.py`: Loads raw CSVs (prices, weather, etc.) and merges them into a single hourly DataFrame.
*   `pipeline/feature_engineering.py`: Creates lag, rolling, calendar, and weather features.
*   `pipeline/dataset_split.py`: Splits the dataset into training and testing sets based on time, per zone.
*   `pipeline/model_train.py`: Trains the CatBoost model, saves the model, and calculates feature importance. Also handles database insertion for predictions and evaluation metrics.
*   `pipeline/forecast.py`: Generates recursive multi-step forecasts for specific zones.
*   `pipeline/evaluate.py`: Computes RMSE, MAE, and MAPE for forecasts against actual values.

---

## 6. Dataset Splitting

*   **Method:** Time-based split per bidding zone.
*   **Default Test Horizon:** `168` hours (7 days).
*   **Principle:** No random shuffling is performed to prevent data leakage and ensure realistic time series evaluation.

---

## 7. Model Specification

### Model

The core forecasting model is a **CatBoostRegressor**.

### Configuration

```python
CatBoostRegressor(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    loss_function='RMSE',
    verbose=0,
    random_seed=42,
    early_stopping_rounds=50
)
```

### Categorical Features

The model handles the following features as categorical:
*   `hour`
*   `weekday`
*   `month`
*   `is_weekend`

---

## 8. Forecasting Strategy

### Rolling Monthly Forecast (Daily Update)

*   **Cadence:** Each day, a new forecast is generated.
*   **Origin Timestamp:** `origin_timestamp` is set to the latest available actual data.
*   **Forecast Horizon:** `origin_timestamp + 1h` up to `origin_timestamp + 720h` (30 days).
*   **Storage:** The `origin_timestamp`, `predicted_timestamp`, and `lead_time` are stored for traceability.

### Forecast Method

*   **Recursive Multi-step:** For each forecasting step, the model predicts the next hour's price. This prediction is then appended to the historical data, and lag features are updated based on this new point before predicting the subsequent hour. This process repeats for the entire horizon.

**Current Limitation:** Exogenous variables are currently forward-filled.
**Future Improvement:** Replace with actual forecasted exogenous inputs (e.g., from MET API weather forecasts).

---

## 9. Storage Architecture

In adherence to the project's **CSV-based storage mandate (no databases for primary pipeline outputs)**, all intermediate and final data outputs from the core pipeline (`data_loader.py`, `feature_engineering.py`, `evaluate.py`) are stored as CSV files.

However, for **tracking forecasts and evaluation results for monitoring and historical analysis**, a SQLite database is used.

*   **Database:** `data/sqlite/forecast_tracking.db`

*   **Table: `forecast_predictions`**
    *   Stores all generated predictions.
    *   `timestamp` (TIMESTAMP, PRIMARY KEY)
    *   `zone` (TEXT)
    *   `predicted_price` (REAL)
    *   `origin_timestamp` (TIMESTAMP)
    *   `lead_hours` (INTEGER)

*   **Table: `forecast_evaluation`**
    *   Stores the comparison between predicted and actual values for evaluation.
    *   `timestamp` (TIMESTAMP, PRIMARY KEY)
    *   `zone` (TEXT)
    *   `actual_price` (REAL)
    *   `predicted_price` (REAL)
    *   `abs_error` (REAL)
    *   `error` (REAL)
    *   `lead_hours` (INTEGER)
    *   `origin_timestamp` (TIMESTAMP)

---

## 10. Evaluation Strategy

### True Month-Ahead Evaluation

For each actual timestamp `T`, the system matches the prediction from the forecast run where `origin_timestamp = T - 720 hours` and `predicted timestamp = T`. This ensures evaluation reflects true long-term forecasting performance.

### Metrics

*   Mean Absolute Error (MAE)
*   Root Mean Squared Error (RMSE)
*   Mean Absolute Percentage Error (MAPE)

### Daily Monitoring System Steps

1.  Ingest latest price and exogenous data.
2.  Update features for the new data.
3.  Run a 30-day forecast.
4.  Store predictions in `forecast_predictions` (SQLite).
5.  Load actual data for the evaluation period.
6.  Evaluate only `lead_hours = 720` (month-ahead).
7.  Store evaluation results in `forecast_evaluation` (SQLite).
8.  Export key evaluation metrics to CSV.

### CSV Outputs

*   `output/predictions_all_zones.csv`: Contains the latest full forecast.
*   `output/feature_importance.csv`: Feature importance scores from the trained model.
*   `output/evaluation_metrics.csv`: Summary of evaluation metrics.

---

## 11. Execution

The full pipeline can be executed via a Python script or daily ingestion batch file.

*   **Full Pipeline (Python):**
    ```bash
    python run_pipeline.py
    ```
*   **Daily Ingestion (Windows Batch):**
    ```bash
    pipeline/run_daily_ingestion.bat
    ```

---

## 12. Deployment

The system supports containerized deployment using Docker and can be integrated into CI/CD pipelines like GitHub Actions.

*   **Docker:**
    ```bash
    docker-compose up --build
    ```
*   **GitHub Actions:**
    Refer to `.github/workflows/docker_pipeline.yml` and `no2_pipeline.yml`.

---

## 13. Advanced System Enhancements (Future Improvements)

### Backtesting Engine (CRITICAL)

*   **Objective:** Evaluate model performance across multiple historical time windows using realistic forecasting scenarios (rolling origin evaluation).
*   **Implementation:** Create `pipeline/backtest.py`.
*   **Benefits:** Detect overfitting, validate stability across seasons, benchmark model improvements.

### SHAP Feature Importance Tracking

*   **Objective:** Understand why the model predicts what it predicts, enabling interpretability, debugging, and trust.
*   **Implementation:** Create `pipeline/shap_analysis.py`.
*   **Outputs:** `output/shap_values_NO2.csv` (feature, shap_value, timestamp) and aggregated mean absolute SHAP values.
*   **Use Cases:** Identify dominant drivers, detect feature drift, validate new features.

### Exogenous Variable Forecasting (CRITICAL UPGRADE)

*   **Current Limitation:** Exogenous variables are currently forward-filled, which degrades long-horizon forecast quality.
*   **Recommended Fix:** Replace historical weather with forecasted weather from APIs (e.g., MET Norway API) or build separate forecast models for exogenous inputs.
*   **Implementation:** Modify `forecast.py` to use forecasted exogenous inputs.
*   **Benefits:** Massive improvement in long-horizon forecasts, more realistic predictions.

---

## 14. Streamlit Dashboard (Live Monitoring)

A Streamlit dashboard can provide a real-time, interactive interface for monitoring and visualizing forecasts.

### Project Structure

```
dashboard/
├── app.py
├── utils.py
└── requirements.txt
```

### Installation

```bash
pip install streamlit pandas plotly sqlite3
```
(Ensure these are also in `dashboard/requirements.txt`)

### Run the Dashboard

From the project root:

```bash
streamlit run dashboard/app.py
```
The dashboard will open in your browser, typically at `http://localhost:8501`.

### Data Sources Used

The dashboard reads data from:
*   **SQLite:** `data/sqlite/forecast_tracking.db` (tables: `forecast_predictions`, `forecast_evaluation`)
*   **CSV (optional):** `output/daily_tracking_month_ahead.csv`

### Core Dashboard Features

1.  **Forecast vs Actual Plot:** Time series comparison of predicted and actual prices.
2.  **Error Metrics:** Displays MAE, RMSE, and rolling error.
3.  **30-Day Forecast Visualization:** Shows the full monthly forecast curve.
4.  **Date and Zone Filters:** Allows interactive selection of time ranges and bidding zones.
5.  **Lead-Time Analysis (Advanced):** Visualize error versus forecast horizon (e.g., 1-day, 7-day, 30-day ahead).

### Deployment Options

*   **Local:** `streamlit run dashboard/app.py`
*   **Docker:** Integrate into `Dockerfile` and `docker-compose.yml`.
*   **Cloud:** Deploy to Streamlit Cloud, Azure Web App, AWS.

### Best Practices

*   Cache database reads (`@st.cache_data`).
*   Avoid loading full datasets; use filtering.
*   Precompute metrics in SQLite for faster dashboards.
*   Use UTC timestamps consistently.

### Future Dashboard Enhancements

*   SHAP visualizations for interpretability.
*   Drift detection charts.
*   Error heatmaps (e.g., hour vs weekday).
*   Multi-zone comparison.
*   Alerting UI for high error spikes.

---

## 15. Critical Engineering Notes

*   **Data Leakage Prevention:** Rolling features use `.shift(1)`, and no future data is used in training.
*   **Recursive Prediction Risk:** Errors accumulate over time, making month-ahead forecasts inherently noisier.
*   **Time Handling:** All timestamps must be UTC timezone-aware.
*   **CSV-Based Storage:** Primary pipeline outputs are CSV-based, aligning with `no2_forcasting/GEMINI.md` mandates. SQLite is used for prediction and evaluation tracking.

---

## 16. System Summary

This system provides:
*   ✔ Rolling daily 30-day forecasts.
*   ✔ CatBoost-based regression model.
*   ✔ Recursive time-series prediction.
*   ✔ True month-ahead evaluation.
*   ✔ Full traceability via SQLite for forecast/evaluation tracking.
*   ✔ Exportable CSV data for visualization.

---

## 17. Status

The system is:
*   ✅ **Fully production-capable.**
*   ✅ **Ready for daily execution.**
*   ✅ **Extensible** for advanced modeling and enhancements.

---
