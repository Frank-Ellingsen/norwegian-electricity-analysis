# 🇳🇴 Norwegian Electricity Spot Price Analysis (2021-2026)

[![Power BI](https://img.shields.io/badge/Dashboard-Power%20BI-yellow)](./Powerbi-Norwegian%20Electricity%20Spot%20Price%20Analysis.pdf)
[![Python](https://img.shields.io/badge/Analysis-Python-blue)](./requirements.txt)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

A comprehensive time-series analysis and forecasting project investigating the volatile electricity market in Norway, focusing on regional price divergence (North vs. South) and seasonal patterns.

## 📊 Portfolio Showcase
**[View the Web Portfolio Page](https://Frank-Ellingsen.github.io/norwegian-electricity-analysis/)**

---

## 🎯 Project Overview
This project analyzes Norwegian electricity prices to understand seasonal patterns, regional price gaps, and predict short-term movements. The analysis focuses on the five Norwegian price zones (NO1-NO5) using data from ENTSO-E and Nord Pool.

### Key Business Question
> *How do regional grid constraints and seasonal weather patterns drive price divergence in the Norwegian electricity market?*

---

## 💡 Key Insights (2021-2026)

| Metric | North (Avg) | South (Avg) | Gap |
| :--- | :--- | :--- | :--- |
| **Price (EUR/MWh)** | **31.34** | **90.09** | **58.75** |

- **Price Convergence Rate:** 187.5%
- **Volatility:** Extreme spikes exceeding **800 EUR/MWh** observed in Southern regions during winter.
- **Drivers of Spikes:** Extreme weather (heating demand), Hydrological balance (reservoir levels), and Interconnector exposure to European markets (UK/Germany).
- **Price Convergence Factors:** High renewable output in Europe, Statnett grid upgrades, and periods of extremely low demand (mild spring weekends).

---

## 🛠️ Tech Stack & Methodology
- **Data Engineering:** Python, SQLite, API Integration (ENTSO-E, Nord Pool)
- **Time-Series Analysis:** Statsmodels (ARIMA/SARIMA), Seasonal Decomposition
- **Visualization:** Power BI Desktop, Matplotlib, Seaborn
- **Frameworks:**
  - **A.I.M** (Ask, Investigate, Model)
  - **C.L.E.A.R** (Context, Logic, Evidence, Action, Results)
  - **B.R.I.D.GE** (Background, Requirements, Insights, Data, Graphics, Execution)

---

## 🏗️ Repository Structure
```text
norwegian-electricity-analysis/
├── data/                        # Processed CSVs and SQLite Database
├── norwegian_powerbi_package/   # DAX measures and Power BI templates
├── visuals/                     # Matplotlib/Seaborn exported plots
├── index.html                   # Portfolio landing page
├── norwegian-electricity-analysis.pbix  # Full Power BI File
└── requirements.txt             # Python dependencies
```

---

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/[YOUR-USERNAME]/norwegian-electricity-analysis.git
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Explore the Data:**
   Open `data/electricity_prices.db` using any SQLite viewer or use the provided scripts to query daily/monthly aggregates.
4. **View the Dashboard:**
   Open `norwegian-electricity-analysis.pbix` in Power BI Desktop or view the [PDF Report Summary](./Powerbi-Norwegian%20Electricity%20Spot%20Price%20Analysis.pdf).

---

## 📝 Methodology
The project follows a rigorous time-series workflow:
1. **ETL:** Automated fetching from Utilitarian Spot API/ENTSO-E.
2. **EDA:** Decomposition of prices into Trend, Seasonal, and Residual components.
3. **Modeling:** Comparison of SARIMA and Prophet models for short-term forecasting.
4. **Storytelling:** Visualizing the "North-South Divide" to explain market dynamics to stakeholders.

---

## 📄 License
This project is open-source and available under the MIT License. Data used is subject to CC BY 4.0 from ENTSO-E.

**Author:** Frank Ellingsen
**Contact:** [Your Email/LinkedIn]
