# 🌍 NO2 Energy Forecasting Pipeline — GEMINI.md  
**Purpose:** Provide a unified instruction layer for AI assistants (Copilot, Gemini CLI, VS Code Agents) working on this project.  
**Scope:** Nord Pool + MET + ENTSO‑E + NVE ingestion, feature engineering, CatBoost forecasting, evaluation, and automation.

---

# 1. 🎯 PROJECT OVERVIEW (A.I.M Framework)

## **A — Aim**
Build a production‑grade forecasting system for the NO2 bidding zone using:
- Nord Pool spot prices  
- MET weather forecasts  
- ENTSO‑E flows & capacities  
- NVE hydrology  
- CatBoost regression  
- Modular, governed, CSV‑based pipelines  

## **I — Inputs**
- APIs: Nord Pool, MET, ENTSO‑E, NVE  
- Historical & forecast weather  
- Cross‑border flows & NTC  
- Hydrology (reservoir, inflow, SWE)  
- Calendar features  
- Lag & rolling features  

## **M — Method**
- Automated ingestion  
- Feature engineering  
- Time‑based splits  
- CatBoost training  
- Rolling multi‑step forecasting  
- Evaluation (RMSE, MAE, MAPE)  
- Export to CSV for Power BI  

---

# 2. 🧱 PROJECT STRUCTURE (C.L.E.A.R Framework)

## **C — Context**
This project forecasts hourly NO2 prices using exogenous drivers from multiple APIs.  
All modules must remain:
- deterministic  
- reproducible  
- CSV‑based  
- production‑safe  

## **L — Layout**
/no2_forecasting/
api/
nordpool_api.py
met_api.py
entsoe_api.py
nve_api.py
pipeline/
data_loader.py
feature_engineering.py
dataset_split.py
model_train.py
forecast.py
evaluate.py
models/
catboost_no2.cbm
output/
predictions_no2.csv
feature_importance.csv
GEMINI.md


## **E — Expectations**
AI assistants must:
- follow modular architecture  
- maintain explicit logging  
- avoid silent failures  
- use robust error handling  
- generate production‑grade code  
- respect CSV‑based storage (no DB)  

## **A — Actions**
AI agents may:
- generate Python modules  
- refactor code  
- add new API integrations  
- optimize CatBoost  
- add backtesting  
- add hyperparameter tuning  
- generate Power BI‑ready outputs  

## **R — Results**
Deliver:
- reproducible forecasts  
- clean code  
- governed data ingestion  
- explainable feature importance  
- stable model performance  

---

# 3. 🧠 AGENT BEHAVIOR RULES (B.R.I.D.GE Framework)

## **B — Boundaries**
Agents must NOT:
- introduce databases  
- remove logging  
- create hidden state  
- break modularity  
- use non‑deterministic randomness  

## **R — Reasoning**
Agents must:
- explain design choices  
- justify model parameters  
- document assumptions  
- prefer clarity over cleverness  

## **I — Interaction**
Agents should:
- ask clarifying questions when needed  
- propose improvements  
- maintain consistent naming conventions  
- follow Python best practices  

## **D — Decomposition**
All tasks must be broken into:
1. Data ingestion  
2. Feature engineering  
3. Splitting  
4. Training  
5. Forecasting  
6. Evaluation  
7. Export  

## **G — Governance**
- All API calls must include error handling  
- All outputs must be timestamped  
- All transformations must be traceable  
- All models must be saved with versioning  

## **E — Execution**
Agents must:
- write clean, production‑ready Python  
- include docstrings  
- include logging  
- avoid unnecessary dependencies  

---

# 4. 🔌 DATA SOURCES & REQUIREMENTS

## **Nord Pool**
- Endpoint: marketdata/page/10  
- Extract hourly NO2 prices  
- Convert to float  
- Index by timestamp  

## **MET Norway**
- Endpoint: locationforecast/2.0/compact  
- Required fields: temperature, wind, precipitation  
- Must include User‑Agent header  

## **ENTSO‑E**
- Required: API key  
- Fetch flows (A11) and NTC (A31)  
- Borders:
  - SE3 → NO2  
  - NO1 → NO2  

## **NVE Hydrology**
- Endpoint: hydapi.nve.no  
- Series:
  - 1000 reservoir  
  - 1001 inflow  
  - 1002 SWE  

---

# 5. 🧮 FEATURE ENGINEERING RULES

## **Lag Features**
- lag_1  
- lag_24  
- lag_168  

## **Rolling Windows**
- roll_mean_24  
- roll_std_24  

## **Calendar Features**
- hour  
- weekday  
- month  
- is_weekend  

## **Exogenous Features**
- weather  
- flows  
- capacities  
- hydrology  

## **Cleaning**
- Drop rows with NaN after lagging  
- Sort index  

---

# 6. 🤖 MODELING RULES (CatBoost)

## **Model Requirements**
- CatBoostRegressor  
- RMSE loss  
- Categorical features:
  - weekday  
  - month  
  - is_weekend  

## **Training Rules**
- Use early stopping  
- Save model to `/models/catboost_no2.cbm`  
- Log training progress  

## **Forecasting Rules**
- Rolling multi‑step  
- Recompute lags at each step  
- Append predictions to dataframe  

---

# 7. 📊 EVALUATION RULES

Metrics:
- RMSE  
- MAE  
- MAPE  

Outputs:
- /output/predictions_no2.csv  
- /output/feature_importance.csv  

---

# 8. 🧪 TESTING & VALIDATION

Agents must:
- validate API responses  
- test feature engineering on sample data  
- ensure forecasting loop works for 24–168 hours  
- verify CSV outputs  

---

# 9. 🧩 EXTENSION MODULES (Optional)

Agents may add:
- Optuna hyperparameter tuning  
- Backtesting engine  
- Power BI export  
- Multi‑zone support (NO1–NO5)  
- Model comparison (CatBoost vs LGBM vs XGB)  

---

# 10. 💡 BRAINSTORMING MODULE

Use this section to generate:
- new feature ideas  
- new exogenous drivers  
- new model architectures  
- new evaluation strategies  
- new visualizations  

Template:
dea
Short description.

Why it matters
Impact on accuracy or interpretability.

How to implement
Steps, modules, dependencies.

Risks
Data quality, API limits, overfitting, etc.


---

# 11. ✔ AGENT CHECKLIST

Before completing any task, agents must confirm:
- [ ] Code is modular  
- [ ] Logging is explicit  
- [ ] No silent failures  
- [ ] CSV outputs are correct  
- [ ] API calls have error handling  
- [ ] Naming conventions are consistent  
- [ ] Comments and docstrings included  

---

# 12. 📌 FINAL NOTE

This GEMINI.md governs **all AI‑assisted work** in this repository.  
All agents must follow it strictly to ensure consistency, quality, and production‑grade outputs.

