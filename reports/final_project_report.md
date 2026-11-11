# Final Project Report & Internship Milestone Delivery
## AI-Powered Job Market Intelligence & Salary Prediction System

**Document Version:** 1.0.0  
**Status:** Completed, Verified & Shipped  
**Scope:** Individual Data Science Internship Project (45-Day Development Plan)  
**Test Suite:** **86 / 86 Unit & Integration Tests Passing** (100% Pass Rate in 11.62s)  
**Live UI:** Streamlit SaaS Dashboard (`dashboard/app.py`) & FastAPI REST API (`api/main.py`)  

---

## 1. Executive Summary

The **AI-Powered Job Market Intelligence & Salary Prediction System** delivers a production-grade data science application designed to resolve information asymmetry, compensation obscurity, and technical skill mismatches across the Indian technology recruitment ecosystem.

The system encompasses six interconnected modules:
1. **Data Collection & Exploratory Analysis:** Cleaned 31,150 raw records into 30,250 standardized postings across 16 hiring cities and 12 canonical roles.
2. **Salary Prediction System:** Trained and calibrated a Tuned XGBoost Regressor with $\log(1+y)$ formulation, achieving a **Test MAE of 2.25 LPA and $R^2$ of 0.6250** with empirical $90\%$ prediction intervals.
3. **Resume Skill Extraction:** Implemented an in-memory PyMuPDF document parser extracting 42 canonical skills across 5 standard resume sections with zero disk retention.
4. **Skill Gap Analysis:** Developed an empirical role benchmarking engine calculating demand-weighted match scores and prioritized upskilling pathways.
5. **Database & REST Microservice:** Architected a 4-table SQLAlchemy 2.0 ORM schema (PostgreSQL with SQLite fallback) and a 9-endpoint FastAPI backend.
6. **Premium Streamlit SaaS Dashboard:** Built an interactive, dark navy (`#0B1020`) user interface with 8 navigation sections, real-time filtering, Plotly visualizations, and live model inference.

---

## 2. Completed Modules & Deliverables Inventory

| Module | Core Deliverables | Verification Status | Artifacts & Reports |
| :--- | :--- | :---: | :--- |
| **Module 1: Data Collection & EDA** | Preprocessing pipeline, text cleaner, 10 distribution plots, master report. | **100% Verified** | `data/processed/cleaned_job_market_all.csv`<br>`reports/figures/eda/` |
| **Module 2: Salary Prediction** | 113-feature pipeline, 5 models compared, Tuned XGBoost (`log1p`), evaluation plots. | **100% Verified** | `models/best_salary_model.joblib`<br>`models/feature_pipeline.joblib` |
| **Module 3: Resume Skill Extraction**| PyMuPDF parser, 5 sections, 42 skills, zero PII retention, 15 tests. | **100% Verified** | `src/resume_parser.py`<br>`reports/resume_extraction_report.md` |
| **Module 4: Skill Gap Analysis** | Role demand profiling, weighted match score, prioritized learning paths. | **100% Verified** | `src/skill_analyzer.py`<br>`reports/skill_gap_analysis_report.md` |
| **Module 5: DB & REST API** | SQLAlchemy 2.0 models, batch ingestion, 9 FastAPI endpoints. | **100% Verified** | `database/db.py`<br>`api/main.py`<br>`reports/job_market_intelligence_report.md` |
| **Module 6: Interactive Dashboard** | 8 Streamlit pages, dark theme (`#0B1020`), Plotly charts, live prediction. | **100% Verified** | `dashboard/app.py`<br>`reports/screenshots/dashboard_overview.png`<br>`reports/dashboard_implementation_report.md` |

---

## 3. Dataset Characteristics & Data Cleaning Funnel

All analytics and modeling are founded on two verified datasets:

```
[ Raw Messy Dataset: 31,150 Records ]
                │
                ▼ Purged Exact Duplicate Rows (-900)
[ Cleaned Market Dataset: 30,250 Postings across 16 Cities & 12 Roles ]
                │
                ├─► Retained for Market Intelligence & Skill Demand (30,250 Postings)
                │
                ▼ Segregated Missing Salary Records (-12,145)
[ Initial Salary Records: 18,105 Postings ]
                │
                ▼ Filtered Inverted/Negative Bounds & Outliers (-546)
[ High-Integrity Salary Modeling Dataset: 17,559 Postings (Target: salary_mid_lpa) ]
```

### Key Statistical Parameters:
- **Cleaned Market Volume:** 30,250 records across 16 Indian cities.
- **Top 3 Roles:** `Business Analyst` (2,604), `BI Developer` (2,586), `Cloud Engineer` (2,562).
- **Top 3 Cities:** `Bengaluru` (2,117), `Delhi NCR` (2,022), `Hyderabad` (2,017).
- **Work Mode Shares:** On-site (42.26%), Hybrid (34.88%), Remote (21.47%).
- **Verified Salary Range:** Median **₹10.50 LPA**, Mean **₹11.83 LPA**, IQR **₹6.50 – ₹16.00 LPA**.
- **Highest Median Roles:** `AI Engineer` (**15.08 LPA**), `MLOps Engineer` (**14.79 LPA**), `ML Engineer` (**14.12 LPA**).

---

## 4. Machine Learning Model Evaluation & Benchmarks

Five regression algorithms were trained and cross-validated across raw and log-transformed targets on an 80/20 split (14,047 training, 3,512 test records):

| Model Name | Target Formulation | CV MAE (LPA) | CV $R^2$ | Test MAE (LPA) | Test RMSE (LPA) | Test $R^2$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Tuned XGBoost Regressor** | **Log-Transformed ($\log(1+y)$)** | **2.29** | **0.6268** | **2.25** | **4.55** | **0.6250** |
| Linear Regression | Log-Transformed ($\log(1+y)$) | 2.27 | 0.6278 | 2.24 | 4.57 | 0.6222 |
| Gradient Boosting Regressor | Log-Transformed ($\log(1+y)$) | 2.31 | 0.6211 | 2.25 | 4.57 | 0.6224 |
| XGBoost Regressor | Raw (`salary_mid_lpa`) | 2.35 | 0.6196 | 2.34 | 4.58 | 0.6198 |
| Gradient Boosting Regressor | Raw (`salary_mid_lpa`) | 2.39 | 0.6060 | 2.35 | 4.61 | 0.6150 |
| Random Forest Regressor | Raw (`salary_mid_lpa`) | 2.44 | 0.6103 | 2.42 | 4.68 | 0.6043 |
| Random Forest Regressor | Log-Transformed ($\log(1+y)$) | 2.41 | 0.6104 | 2.38 | 4.70 | 0.6001 |
| Linear Regression | Raw (`salary_mid_lpa`) | 2.55 | 0.5978 | 2.53 | 4.75 | 0.5917 |
| Decision Tree Regressor | Log-Transformed ($\log(1+y)$) | 2.72 | 0.5356 | 2.81 | 5.53 | 0.4456 |
| Decision Tree Regressor | Raw (`salary_mid_lpa`) | 2.80 | 0.5169 | 2.92 | 5.64 | 0.4244 |

### Champion Model Selection & Residual Spread:
- **Selected Champion:** Tuned XGBoost Regressor ($\log(1+y)$).
- **Test Metrics:** MAE = **2.25 LPA**, RMSE = **4.55 LPA**, $R^2 = \mathbf{0.6250}$.
- **Residual Standard Deviation:** $s_{\text{resid}} = 4.53\text{ LPA}$.
- **Uncertainty Bounds:** Point estimates are accompanied by empirical $90\%$ confidence bounds:
  $$\hat{y} \pm 1.645 \times 4.53 = \hat{y} \pm 7.45\text{ LPA}$$

---

## 5. Automated Pytest Verification Summary

The project test suite contains **86 automated unit and integration tests**:

```powershell
pytest -v
============================= 86 passed in 11.62s =============================
```

- `tests/test_preprocessing.py`: 9 passed
- `tests/test_feature_engineering.py`: 3 passed
- `tests/test_salary_model.py`: 10 passed
- `tests/test_resume_parser.py`: 15 passed
- `tests/test_skill_analyzer.py`: 16 passed
- `tests/test_job_market_intelligence.py`: 8 passed
- `tests/test_database.py`: 6 passed
- `tests/test_api.py`: 9 passed
- `tests/test_dashboard.py`: 10 passed
- **Pass Rate:** **100% (86 / 86)** with **0 failed and 0 skipped**.

---

## 6. Known Technical Limitations & Governance

1. **Local PostgreSQL Service Configuration:**
   - The background Windows PostgreSQL service requires private credentials.
   - The system operates with full ORM compatibility on SQLite (`data/job_market.db`), with database status clearly disclosed in the UI sidebar and `/health` response.
2. **Academic & Simulated Dataset Scope:**
   - The underlying dataset is synthetically generated for educational Data Science internship demonstration. While its distributions and skill co-occurrences reflect realistic Indian technology hiring patterns, no individual company, salary, or posting constitutes live corporate data.
3. **Resume Document Constraints:**
   - Scanned or image-only PDFs lacking a selectable text layer cannot be parsed without OCR; the system gracefully returns a helpful OCR limitation message.

---

## 7. Delivery Status

All 10 steps of the project plan are complete, fully tested, documented, and ready for version control and assessment.

