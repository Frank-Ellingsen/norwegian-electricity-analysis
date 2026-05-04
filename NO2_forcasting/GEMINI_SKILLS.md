# 🧠 GEMINI_SKILLS.md  
Skill definitions for AI assistants collaborating on the NO2 Energy Forecasting Pipeline.

This file defines **capabilities**, **constraints**, and **extension patterns** for agents working within this repository.  
It complements the governance rules in `GEMINI.md`.

---

# 1. 🔌 DATA INGESTION SKILLS

## **Skill: Fetch Nord Pool Prices**
**Description:** Retrieve hourly NO2 spot prices from Nord Pool API.  
**Agents may:**
- Implement or refactor API calls  
- Add retry logic  
- Add caching  
- Validate timestamps and missing hours  
**Agents must not:**
- Change the API endpoint  
- Introduce databases  

---

## **Skill: Fetch MET Weather**
**Description:** Retrieve weather forecasts (temperature, wind, precipitation) from MET Norway.  
**Agents may:**
- Add new weather variables  
- Add spatial averaging for multiple coordinates  
- Add forecast horizon alignment  
**Agents must not:**
- Remove User-Agent header  
- Introduce non-MET weather sources without approval  

---

## **Skill: Fetch ENTSO‑E Flows & Capacities**
**Description:** Retrieve cross-border flows (A11) and NTC capacities (A31).  
**Agents may:**
- Add new borders (NO1–NO5)  
- Add generation/load data  
- Add XML parsing improvements  
**Agents must not:**
- Hardcode API keys  
- Modify domain codes without documentation  

---

## **Skill: Fetch NVE Hydrology**
**Description:** Retrieve reservoir levels, inflow, SWE from NVE HydAPI.  
**Agents may:**
- Add new hydrology series  
- Add interpolation logic  
- Add weekly-to-hourly alignment  
**Agents must not:**
- Introduce smoothing without explicit instruction  

---

# 2. 🧱 FEATURE ENGINEERING SKILLS

## **Skill: Create Lag Features**
**Description:** Generate lag_1, lag_24, lag_168.  
**Agents may:**
- Add additional lags  
- Add rolling windows  
- Add differencing  
**Agents must not:**
- Remove existing lags  
- Break time alignment  

---

## **Skill: Create Calendar Features**
**Description:** Add hour, weekday, month, is_weekend.  
**Agents may:**
- Add holiday flags  
- Add seasonality encodings  
**Agents must not:**
- Replace calendar features with embeddings  

---

## **Skill: Merge Exogenous Drivers**
**Description:** Combine weather, flows, capacities, hydrology.  
**Agents may:**
- Add new exogenous sources  
- Add normalization/scaling  
**Agents must not:**
- Drop exogenous variables without justification  

---

# 3. 🤖 MODELING SKILLS

## **Skill: Train CatBoost Model**
**Description:** Train CatBoostRegressor with RMSE loss.  
**Agents may:**
- Tune hyperparameters  
- Add Optuna search  
- Add model versioning  
**Agents must not:**
- Replace CatBoost with another model family unless explicitly requested  

---

## **Skill: Rolling Multi-Step Forecasting**
**Description:** Generate 24–168 hour forecasts using recursive predictions.  
**Agents may:**
- Add probabilistic forecasting  
- Add quantile outputs  
- Add scenario generation  
**Agents must not:**
- Replace recursive forecasting with direct multi-output without approval  

---

# 4. 📊 EVALUATION SKILLS

## **Skill: Compute Metrics**
**Description:** RMSE, MAE, MAPE.  
**Agents may:**
- Add SMAPE  
- Add cross-validation  
- Add backtesting  
**Agents must not:**
- Remove RMSE  

---

## **Skill: Feature Importance**
**Description:** Extract CatBoost feature importance.  
**Agents may:**
- Add SHAP values  
- Add permutation importance  
**Agents must not:**
- Remove feature importance export  

---

# 5. 🧩 PIPELINE EXTENSION SKILLS

## **Skill: Add New Zones (NO1–NO5)**
**Description:** Generalize pipeline to all bidding zones.  
**Agents may:**
- Add dynamic zone selection  
- Add zone-specific exogenous drivers  
**Agents must not:**
- Hardcode zone logic  

---

## **Skill: Add Power BI Export**
**Description:** Create clean CSVs for BI dashboards.  
**Agents may:**
- Add hourly forecast tables  
- Add metadata columns  
**Agents must not:**
- Introduce proprietary BI formats  

---

## **Skill: Add Automation**
**Description:** Daily retraining, scheduled ingestion.  
**Agents may:**
- Add cron-compatible scripts  
- Add logging improvements  
**Agents must not:**
- Add cloud dependencies without approval  

---

# 6. 🧪 TESTING & VALIDATION SKILLS

## **Skill: Validate API Data**
**Description:** Ensure completeness, continuity, and correctness.  
**Agents may:**
- Add anomaly detection  
- Add missing-hour repair  
**Agents must not:**
- Ignore API errors  

---

## **Skill: Validate Forecast Quality**
**Description:** Ensure model performance is stable.  
**Agents may:**
- Add drift detection  
- Add rolling RMSE tracking  
**Agents must not:**
- Remove evaluation steps  

---

# 7. 🧠 BRAINSTORMING SKILLS

## **Skill: Generate Feature Ideas**
**Description:** Propose new exogenous drivers or transformations.  
**Agents may:**
- Suggest hydrology derivatives  
- Suggest weather interactions  
**Agents must not:**
- Add features without documenting rationale  

---

## **Skill: Model Improvement Proposals**
**Description:** Suggest enhancements to accuracy or stability.  
**Agents may:**
- Propose hybrid models  
- Propose ensemble strategies  
**Agents must not:**
- Replace CatBoost without explicit instruction  

---

# 8. ✔ AGENT CHECKLIST FOR ALL SKILLS

Before completing any task, agents must confirm:
- [ ] Code is modular  
- [ ] Logging is explicit  
- [ ] No silent failures  
- [ ] CSV outputs preserved  
- [ ] API calls validated  
- [ ] Time alignment correct  
- [ ] No breaking changes introduced  

---

# 9. 📌 FINAL NOTE

This file defines the **skill boundaries** for all AI agents working in this repository.  
Agents must follow these rules to ensure consistency, reliability, and production‑grade quality.

