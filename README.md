# Norwegian Electricity Time‑Series Analysis & Forecasting

## Overview
This repository contains a reproducible pipeline for analyzing and forecasting Norwegian electricity prices and consumption. The project uses public data sources, Python-based ETL, SQLite storage, and Power BI reporting. All workflows follow strict reproducibility, transparency, and documentation standards.

## Objectives
- Build and evaluate time‑series forecasting models.
- Identify seasonal patterns and drivers of electricity prices.
- Produce clean datasets for analysis and reporting.
- Generate Power BI‑ready outputs for visualization.
- Provide portfolio‑ready insights and documentation.

## Tools and Environment
- Python (PEP8, modular scripts, logging)
- SQLite (local analytical store)
- CSV (primary data format)
- Excel (inspection only)
- Visual Studio Code

## Directory Structure
/src        → Python ETL + modeling modules
/data       → raw + processed CSVs
/analysis   → notebooks, EDA, decomposition
/visuals    → plots, Power BI exports
/docs       → GEMINI.md, skill.md, methodology

Code

## Data Workflow
1. Ingest raw CSV files from `/data/raw/`.
2. Clean, transform, and validate data.
3. Store processed outputs in `/data/processed/`.
4. Load data into SQLite for analysis and reporting.
5. Generate forecast tables and plots.
6. Export Power BI‑ready datasets.

## Modeling Approach
- Baseline models: naive, moving average  
- Classical models: ARIMA, SARIMA  
- Optional: Prophet  
- Evaluation metrics: RMSE, MAE, MAPE  
- Outputs: forecast tables, plots, decomposition, insights  

## Documentation
All methodology, frameworks, and agent rules are located in `/docs`, including:
- `GEMINI.md`
- `skill.md`
- Methodology notes
- Project instructions

## Contribution Guidelines
See `CONTRIBUTING.md` for rules on commits, branching, pull requests, and documentation.

## License
No license is assumed. Do not add or modify license files unless explicitly instructed.
CONTRIBUTING.md
markdown
# Contributing Guidelines