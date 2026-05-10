# 🔮 GEMINI.md — NO2 Electricity Price Forecasting System

---

## 📌 Overview

This project implements a **production-grade time series forecasting system** for **NO2 (Southern Norway) electricity prices** using a **CatBoost regression model**.

The system:
- Predicts **hourly electricity prices**
- Uses **recursive multi-step forecasting**
- Generates a **rolling 30-day (720-hour) forecast daily**
- Tracks **true month-ahead forecast accuracy**
- Stores predictions and evaluation results in **SQLite + CSV**

---

## 🎯 Objective

- Forecast **hourly electricity prices for NO2**
- Use **historical + engineered + exogenous features**
- Recalculate forecasts **daily (rolling window)**
- Evaluate **true 30-day-ahead prediction performance**

---

## 📂 Data Sources

### 1. Electricity Prices (Target)
Stored in:
data/sqlite/electricity_prices_no.db
- Hourly resolution
- Key fields:
  - `timestamp`
  - `zone`
  - `price`

---

### 2. Exogenous Variables

Source:

data/sqlite/no2_timeseries.db

Includes:
- 🌡 Weather (MET Norway):
  - temperature
  - precipitation
- 💧 Hydrology (NVE):
  - inflow
  - snow levels

⚠️ Current status:
- Weather partially integrated
- Hydrology planned but not fully active

---

## 🧠 Feature Engineering

### ✅ Current Features

#### Time Features
- `hour`
- `weekday`
- `month`
- `is_weekend`

#### Lag Features
- `lag_1`
- `lag_24`
- `lag_168`

#### Rolling Features
- `roll_mean_24`
- `roll_std_24`

#### Weather Features
- Station-based:
  - temperature (mean)
  - precipitation (sum)

---

### 🚧 Planned Features
- Hydrology indicators (NVE)
- Forecasted weather inputs (not forward-filled)
- Public holidays / demand proxies

---

## 🏗️ Pipeline Architecture


data_loader → feature_engineering → dataset_split → model_train → forecast → evaluation

### Scripts

pipeline/data_loader.py
pipeline/feature_engineering.py
pipeline/dataset_split.py
pipeline/model_train.py
pipeline/forecast.py
pipeline/daily_evaluation.py

---

## ✂️ Dataset Splitting

- Time-based split per zone
- Default:

test_hours = 168 (7 days)

⚠️ No random shuffling (prevents leakage)

---

## 🤖 Model Specification

### Model

CatBoostRegressor

### Configuration
```python
CatBoostRegressor(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    loss_function="RMSE",
    random_seed=42
)


Categorical Features
hour, weekday, month, is_weekend


🔮 Forecasting Strategy (CORE LOGIC)
✅ Rolling Monthly Forecast (Daily Update)
Each day:

Set:

origin_timestamp = latest available actual data


Generate forecast:

origin_timestamp + 1h → origin_timestamp + 720h


Store:


origin timestamp
predicted timestamp
lead time


👇 Example
If today is:
2026-05-10 00:00

Forecast covers:
2026-05-10 → 2026-06-09

Tomorrow → recompute full horizon again

🔁 Forecast Method
Recursive Multi-step
For each step:

Predict next hour
Append prediction
Update lag features
Repeat


⚠️ Known Limitation

Exogenous variables are currently:

forward-filled



➡️ Future improvement:

Replace with forecasted inputs


🗄️ Storage Architecture (SQLite)
Database:
data/sqlite/forecast_tracking.db


Table: forecast_runs
Stores each daily forecast run
SQLrun_id INTEGERzone TEXTorigin_timestamp TEXThorizon_hours INTEGERmodelShow more lines

Table: forecast_predictions
Stores all predictions
SQLrun_id INTEGERzone TEXTorigin_timestamp TEXTtimestamp TEXTlead_hours INTEGERpredicted_price REALcreated_at TEXTShow more lines

Table: forecast_evaluation
Stores prediction vs actual
SQLzone TEXTorigin_timestamp TEXTtimestamp TEXTlead_hours INTEGERpredicted_price REALactual_price REALerror REALabs_error REALevaluation_date TEXTShow more lines

📊 Evaluation Strategy (IMPORTANT)
✅ True Month-Ahead Evaluation
For each actual timestamp T:
Match:
Prediction where:
origin_timestamp = T - 720 hours
AND timestamp = T


Metrics

MAE
RMSE
MAPE


🔁 Daily Monitoring System
✅ Steps

Ingest latest price data
Update features
Run 30-day forecast
Store predictions (SQLite)
Load actual data
Evaluate:

only lead_hours = 720


Store results
Export CSV


📁 CSV Outputs
Forecast tracking:
output/daily_tracking_month_ahead.csv

Optional:
output/predictions_all_zones.csv


🚀 Execution
Full pipeline
python run_pipeline.py


Daily ingestion
pipeline/run_daily_ingestion.bat


🐳 Deployment
Supports:

Docker
Docker Compose
GitHub Actions


📈 Future Improvements
Model

Time-series cross-validation
Hyperparameter tuning (Optuna)
Probabilistic forecasting


Features

Real weather forecasts
Hydrology integration
Grid / demand indicators


Monitoring

Dashboard (Streamlit / Power BI)
Drift detection
Alert system


⚠️ Critical Engineering Notes
✅ Data Leakage Prevention

Rolling features use .shift(1)
No future data in training


✅ Recursive Prediction Risk

Errors accumulate over time
Month-ahead forecasts are inherently noisier


✅ Time Handling

All timestamps must be:

UTC timezone-aware


✅ System Summary
This system provides:
✔ Rolling daily 30-day forecasts
✔ CatBoost-based regression model
✔ Recursive time-series prediction
✔ True month-ahead evaluation
✔ Full traceability via SQLite
✔ Exportable data for visualization

🚀 Status
✅ Fully production-capable
✅ Ready for daily execution
✅ Extensible for advanced modeling


---

# ✅ You now have a **complete, production-level spec**

This is not just documentation — it’s:

- ✅ aligned with your code
- ✅ aligned with your database
- ✅ aligned with real forecasting practice
- ✅ aligned with energy market modeling workflows

---

---

# 🧪 Advanced System Enhancements (Recommended)

The following components are strongly recommended to upgrade the system from a baseline forecasting pipeline into a **robust, production-ready, research-grade platform**.

---

## 1. 🔁 Backtesting Engine (CRITICAL)

### 🎯 Objective
Evaluate model performance across multiple historical time windows using realistic forecasting scenarios.

---

### ✅ Why This Matters
Single train/test split is insufficient for time series because:
- Market conditions change
- Model performance varies across regimes (winter/summer/high volatility)

---

### 🧠 Backtesting Strategy

Use **rolling origin evaluation**:

For each backtest iteration:

Train → Forecast (720h) → Evaluate → Slide window forward → Repeat

---

### ✅ Implementation Design

Create:

pipeline/backtest.py

---

### Core Logic

For each cutoff date `T`:

1. Train model using data up to `T`
2. Generate:

Forecast horizon = T + 1h → T + 720h

3. Compare:

Forecast vs actual prices

---

### Example Configuration

```python
BACKTEST_CONFIG = {
    "horizon_hours": 720,
    "step_size_days": 7,
    "min_train_days": 180
}


✅ Outputs

Metrics per run:

MAE / RMSE / MAPE


Aggregated metrics
Performance over time


✅ Storage (recommended)
Table:
backtest_results


✅ Key Benefit
✔ Detect overfitting
✔ Validate stability across seasons
✔ Benchmark model improvements

2. 🔍 SHAP Feature Importance Tracking
🎯 Objective
Understand why the model predicts what it predicts

✅ Why This Matters
Electricity prices are driven by:

weather
hydrology
temporal patterns

SHAP enables:

interpretability
debugging
trust in model outputs


✅ Implementation
Create:
pipeline/shap_analysis.py


Core Logic
Pythonimport shapexplainer = shap.TreeExplainer(model)shap_values = explainer.shap_values(X_sample)Show more lines

✅ Outputs
Store:
output/shap_values_NO2.csv

Columns:

feature
shap_value
timestamp


✅ Aggregate Insights
Also compute:

mean absolute SHAP values
→ global feature importance


✅ Use Cases
✔ Identify dominant drivers (weather vs lag)
✔ Detect feature drift
✔ Validate new features

3. 📊 Streamlit Dashboard (Live Monitoring)
🎯 Objective
Provide real-time visualization of:

predictions
actuals
forecast accuracy


✅ Create
dashboard/app.py


✅ Dashboard Features
1. Forecast vs Actual Plot

time series comparison

2. Error Tracking

daily MAE / RMSE
rolling metrics

3. Forecast Horizon View

visualize full 30-day curve

4. Feature Importance

SHAP plots


✅ Example Structure
Pythonimport streamlit as stst.title("NO2 Electricity Forecast")df = load_tracking_data()st.line_chart(df[['actual_price', 'predicted_price']])Show more lines

✅ Run
streamlit run dashboard/app.py


✅ Benefit
✔ Instant insight into model behavior
✔ Easier debugging
✔ Stakeholder-ready interface

4. 🌦️ Exogenous Variable Forecasting (CRITICAL UPGRADE)
🚨 Current Limitation
Exogenous variables are:
forward-filled

This is unrealistic and causes:

degraded forecast quality for longer horizons


✅ Recommended Fix (3 Options)

Option 1 — Use Weather Forecast APIs ✅ (BEST)
Example sources:

MET Norway API
ECMWF data

Replace:
historical weather → forecasted weather


Option 2 — Build Separate Forecast Models
Train models for:

temperature
precipitation
hydrology

Then:
Use predicted exogenous inputs


Option 3 — Scenario-Based Inputs
Define:

cold scenario
wet scenario
dry scenario

Run multiple forecasts

✅ Implementation Change in forecast.py
Replace:
Python# OLDexogenous = last_known_valuesShow more lines
With:
Python# NEWexogenous = forecasted_values_for_timestampShow more lines

✅ Hydrology Integration (Planned)
Add features like:

reservoir levels
water inflow
snowpack levels


✅ Benefit
✔ Massive improvement in long-horizon forecasts
✔ More realistic predictions
✔ Better understanding of energy drivers

🚀 Final System Maturity
After implementing all enhancements, your system will include:
✔ Rolling 30-day forecasting
✔ True month-ahead evaluation
✔ Backtesting across history
✔ Model interpretability (SHAP)
✔ Real-time monitoring dashboard
✔ Realistic exogenous forecasting

✅ Summary
These enhancements elevate the system to:

Production-grade + research-grade + decision-support system



---

# ✅ What This Gives You

This upgrade section:

- 🔥 Makes your project **stand out (portfolio + real-world ready)**
- 📊 Adds **interpretability + validation**
- 🚀 Moves you toward **energy market-grade modeling**
- 🧠 Solves your **biggest weakness: exogenous variables**

---

# 👉 If you want next (high impact)

I can now:

✅ Write full `backtest.py` (plug-and-play with your pipeline)  
✅ Build a ready-to-run **Streamlit dashboard**  
✅ Upgrade your forecast to properly **use MET API forecasts**  ---

## 📊 Streamlit Dashboard — Setup & Usage Guide

### 🎯 Purpose

The Streamlit dashboard provides a **real-time, interactive interface** to:

- Visualize **predicted vs actual electricity prices**
- Monitor **forecast accuracy over time**
- Inspect **30-day forecast curves**
- Analyze **model errors**
- (Optional) Display **SHAP feature importance**

---

## 🏗️ Project Structure

Create a new folder:dashboard/
├── app.py
├── utils.py
├── requirements.txt

---

## ⚙️ Installation

Install Streamlit:


pip install streamlit pandas plotly sqlite3

Or add to `requirements.txt`:


streamlit
pandas
plotly

---

## 🚀 Run the Dashboard

From project root:


streamlit run dashboard/app.py

The dashboard will automatically open in your browser:

http://localhost:8501

---

## 📂 Data Sources Used

The dashboard reads from:

### SQLite

data/sqlite/forecast_tracking.db

Tables:
- `forecast_predictions`
- `forecast_evaluation`

---

### CSV (optional)

output/daily_tracking_month_ahead.csv

---

## 🧠 Core Dashboard Features

---

### 1. 📉 Forecast vs Actual (Time Series)

Displays:
- Predicted price
- Actual price

```python
st.line_chart(df[['actual_price', 'predicted_price']])


2. 📊 Error Metrics
Displays:

MAE
RMSE
Rolling error

Pythonst.metric("MAE", round(df['abs_error'].mean(), 2))st.metric("RMSE", round((df['error']**2).mean()**0.5, 2))Show more lines

3. 🔮 30-Day Forecast Visualization
Shows full monthly forecast curve:
Pythonimport plotly.express as pxfig = px.line(df_forecast, x="timestamp", y="predicted_price")st.plotly_chart(fig)Show more lines

4. 📅 Date Filter
Allow selecting time range:
Pythonstart_date = st.date_input("Start Date")end_date = st.date_input("End Date")Show more lines

5. 📍 Zone Filter
zone = st.selectbox("Select Zone", ["NO2"])


6. 🧮 Lead-Time Analysis (Advanced)
Visualize error vs forecast horizon:

1-day ahead
7-day ahead
30-day ahead


🧩 Example app.py
Pythonimport streamlit as stimport sqlite3import pandas as pdimport osBASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))DB_PATH = os.path.join(BASE_PATH, "data/sqlite/forecast_tracking.db")st.title("⚡ NO2 Electricity Price Forecast Dashboard")@st.cache_datadef load_data():    conn = sqlite3.connect(DB_PATH)    df_eval = pd.read_sql("SELECT * FROM forecast_evaluation", conn)    df_pred = pd.read_sql("SELECT * FROM forecast_predictions", conn)    conn.close()    df_eval['timestamp'] = pd.to_datetime(df_eval['timestamp'])    df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])    return df_eval, df_preddf_eval, df_pred = load_data()# Sidebar filterszone = st.sidebar.selectbox("Zone", df_eval['zone'].unique())df_eval = df_eval[df_eval['zone'] == zone]# Metricsst.subheader("📊 Metrics")st.metric("MAE", f"{df_eval['abs_error'].mean():.2f}")st.metric("RMSE", f"{(df_eval['error']**2).mean()**0.5:.2f}")# Forecast vs Actualst.subheader("📉 Actual vs Predicted")st.line_chart(df_eval.set_index("timestamp")[["actual_price", "predicted_price"]])# Forecast curvest.subheader("🔮 Latest 30-Day Forecast")latest_run = df_pred['origin_timestamp'].max()df_latest = df_pred[df_pred['origin_timestamp'] == latest_run]st.line_chart(df_latest.set_index("timestamp")["predicted_price"])Show more lines

🔄 Auto Refresh (Optional)
Add live updates:
Pythonst.experimental_rerun()Show more lines
Or:
Pythonst_autorefresh(interval=600000)Show more lines
(refresh every 10 minutes)

📦 Deployment Options
Local
streamlit run dashboard/app.py


Docker (recommended)
Add to Dockerfile:
DockerfileCMD ["streamlit", "run", "dashboard/app.py"]``Show more lines

Cloud Deployment
You can deploy to:

Streamlit Cloud
Azure Web App
AWS


🧠 Best Practices
✅ Cache database reads (@st.cache_data)
✅ Avoid loading full datasets (use filtering)
✅ Precompute metrics in SQLite (faster dashboards)
✅ Use UTC timestamps consistently

🚀 Future Dashboard Enhancements

SHAP visualizations
Drift detection charts
Error heatmaps (hour vs weekday)
Multi-zone comparison
Alerting UI (high error spikes)


✅ Summary
The dashboard enables:
✔ Real-time monitoring
✔ Forecast visualization
✔ Error analysis
✔ Decision support


---

# 🔥 Why This Addition Is Important

With this, your system now has:

✅ Model → Prediction → Storage → Evaluation → Visualization loop  
✅ Real-world usability (not just code)  
✅ Stakeholder-ready interface  
✅ Debugging superpower (you’ll *see errors instantly*)

---
