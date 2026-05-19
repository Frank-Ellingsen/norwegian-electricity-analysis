# GEMINI.md — Norwegian Electricity Time‑Series Analysis & Forecasting

## 1. Project overview
- Project Title: Norwegian Electricity Price & Consumption Forecasting
- Primary Goal: Build, evaluate, and explain time‑series models for electricity prices and/or consumption.
- Business Question: How can we forecast short‑term electricity prices/consumption and understand key seasonal patterns?
- Intended Output: Python pipeline, SQLite data store, Power BI dashboard, written insights.
- Tools: Python, SQLite, Excel, Power BI

## 2. Frameworks used
- A.I.M — Ask, Investigate, Model
- C.L.E.A.R — Context, Logic, Evidence, Action, Results
- B.R.I.D.GE — Background, Requirements, Insights, Data, Graphics, Execution
- BRAINSTORM — Divergent → Convergent → Selection → Hypotheses → Risks

## 3. Brainstorming

### Divergent thinking
Ideas:
- Hourly electricity prices by bidding zone.
- Daily average prices and consumption.
- Seasonality (day of week, month, holidays).
- Weather impact (temperature vs consumption).
- Forecast next 7/30 days.
- Scenario analysis: cold vs mild winter.

### Convergent thinking
Criteria:
- Portfolio value: high (energy + forecasting).
- Data availability: good (public sources).
- Technical depth: high (ARIMA/SARIMA/Prophet).
- Storytelling: strong (prices, bills, policy).

### Selected concept
Forecast daily average electricity prices (and optionally consumption) for a Norwegian bidding zone.

### Hypotheses
- Strong weekly and yearly seasonality.
- Winter prices higher and more volatile.
- Linear Regression outperform naive benchmarks.

### Risks
- Missing data or API limits.
- Time zone alignment.
- Weather data alignment (if used).

## 4. A.I.M

### Ask
How accurately can we forecast short‑term electricity prices, and what seasonal patterns drive them?

### Investigate
- Data sources: public electricity price data (e.g., Nord Pool exports), optional weather data.
- Granularity: hourly → aggregated to daily.
- Transformations: resampling, handling missing values, outlier treatment, feature engineering (lags, rolling means).
- Methods: EDA, decomposition, stationarity tests, ARIMA/SARIMA, Prophet, baseline models.

### Model
- Baselines: naive (last value), moving average.
- Classical: ARIMA/SARIMA.
- Modern: Prophet (if installed).
- Evaluation: train/test split, rolling forecast, metrics (RMSE, MAE, MAPE).
- Outputs: forecasts table, plots, Power BI‑ready dataset.

## 5. C.L.E.A.R

- Context: Electricity prices affect households, businesses, and policy decisions.
- Logic: Use historical prices and seasonality to forecast near‑term prices.
- Evidence: Time‑series plots, decomposition, model metrics.
- Action: Use forecasts for planning, budgeting, and scenario analysis.
- Results: Quantified forecast accuracy and visual forecast ranges.

## 6. B.R.I.D.GE

- Background: Volatile electricity prices in Norway/Europe; need for better planning.
- Requirements: Clean time‑series dataset, reproducible pipeline, interpretable models, Power BI dashboard.
- Insights: Seasonality, trend, volatility, forecast ranges.
- Data: Raw CSVs → processed SQLite tables → Power BI model.
- Graphics: Python plots + Power BI visuals (trend, seasonality, forecast).
- Execution: Python ETL + modeling, SQL aggregation, Power BI reporting.

## 7. Agent instructions

You are an Analyst‑Assistant Agent helping build this time‑series project.

### Responsibilities
- Generate clean Python ETL and modeling scripts.
- Write SQL queries for aggregations and features.
- Prepare Power BI‑ready datasets.
- Suggest DAX measures and visuals.
- Produce C.L.E.A.R‑style insight summaries.

### Coding standards
- Python: PEP8, functions, docstrings, logging.
- SQL: CTEs, readable formatting.
- Excel/CSV: clean column names, clear date/time fields.
- Power BI: explicit measures, documented.

### File rules
- Do not overwrite files unless explicitly instructed.
- Use /src, /data, /analysis, /visuals, /docs.
- Comment assumptions and key decisions.

## 8. Output expectations
- Clean time‑series datasets (daily/hourly).
- Python scripts for ETL + modeling.
- SQLite tables for storage and reporting.
- Power BI‑ready tables and measures.
- Insight summaries and methodology docs.
- Portfolio‑ready narrative and visuals.
