# Module 6: Streamlit Interactive SaaS Dashboard Report
## AI-Powered Job Market Intelligence & Salary Prediction System

**Document Version:** 1.0.0  
**Status:** Completed, Integrated & Verified  
**Application Entrypoint:** [`dashboard/app.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/dashboard/app.py)  
**SaaS Theme:** Dark Navy (`#0B1020`), Card Surface (`#151D30`), Electric Blue (`#3B82F6`), Violet (`#8B5CF6`)  
**Automated Test Suite:** `tests/test_dashboard.py` (10 passed)  
**Total Project Suite:** **86 / 86 unit tests passing** (100% pass rate in 11.62s)  

> **Educational & Dataset Scope Disclaimer:** All figures, distributions, salary benchmarks, and analytical insights presented across this application are derived from the supplied simulated dataset (`cleaned_job_market_all.csv` and `cleaned_salary_model_data.csv`). While distributions reflect realistic Indian tech industry compensation and skill demand patterns, they must be interpreted as simulated benchmarks for Data Science internship demonstration, not live macroeconomic statistics or contractual employment guarantees.

---

## 1. Executive Summary & Architecture

Module 6 delivers a modern, responsive, high-performance Streamlit SaaS dashboard that unifies all previously developed analytical engines, machine learning pipelines, NLP document parsers, and database models into an interactive product experience.

### Architectural Layout:
```
dashboard/
├── app.py                      # Main Streamlit router, page configuration & theme initialization
├── data_loader.py              # Centralized caching (@st.cache_data / @st.cache_resource) & health checks
├── assets/
│   └── style.css               # Custom CSS design system (#0B1020 dark theme, card glassmorphism)
├── components/
│   ├── __init__.py
│   ├── layout.py               # Custom CSS injection, headers, alert boxes, disclaimer footers
│   ├── sidebar.py              # Persistent navigation, branding, database & API health indicators
│   ├── metric_cards.py         # SaaS KPI cards with accent borders, tags, and subtitle metadata
│   ├── charts.py               # Dark-themed Plotly charts (bar, donut, histogram, box plot, gauge)
│   ├── filters.py              # Multi-dimensional filter panel (Role, City, State, Exp, Work Mode)
│   └── tables.py               # Formatted DataFrame tables and prioritized recommendation cards
└── pages/
    ├── __init__.py
    ├── overview.py             # Macro market KPIs, role/city distributions, and data-derived insights
    ├── job_market.py           # In-depth role demand rankings, state distributions, skill co-occurrence
    ├── salary_analytics.py     # Verified salary benchmarks (LPA), seniority tiers, and quartiles
    ├── salary_prediction.py    # Interactive form calling Tuned XGBoost inference with 90% confidence bounds
    ├── resume_analyzer.py      # In-memory PDF upload, section segmentation, and skill extraction
    ├── skill_gap.py            # Demand-weighted match score gauge, missing tiers, and learning pathways
    ├── data_quality.py         # Data audit, cleaning funnel, missing values, and salary reconciliation
    └── about.py                # Problem statement, ML methodology, privacy practices, and academic scope
```

---

## 2. Implemented Pages & Core Features

### Page 1: Overview (`dashboard/pages/overview.py`)
- **Executive KPI Cards:**
  - Total Job Postings: **30,250**
  - Unique Recruiting Companies: **16**
  - Canonical Job Roles: **12**
  - Hiring Hubs (Cities): **16**
  - Verified Median Salary: **₹10.50 LPA**
  - Verified Average Salary: **₹11.83 LPA**
- **Visualizations (Plotly Express with dark template `#0B1020`):**
  - Job Postings by Canonical Role (horizontal bar chart)
  - Top 10 Indian Tech Hiring Hubs (vertical bar chart)
  - Work Mode Share (Donut chart: On-site 42.26%, Hybrid 34.88%, Remote 21.47%)
  - Employment Type Share (Donut chart: Full-time 77.86%, Contract 13.36%, Internship 5.80%)
  - Postings by Seniority Level (bar chart)
  - Top 10 In-Demand Technical Skills (bar chart)
- **Data-Derived Observations:** Comprehensive strategic insights highlighting cross-role demand balance, flexible work arrangement preferences, and AI/ML compensation premiums.

### Page 2: Job Market Intelligence (`dashboard/pages/job_market.py`)
- **Integrated Module:** `src/job_market_intelligence.py`
- **Dynamic Multi-Dimensional Filters:** Real-time slicing by Role, City, State, Experience Level, Work Mode, and Employment Type.
- **Dynamic Slicing Metrics:** Live calculation of filtered volume, represented companies, active hubs, and canonical roles.
- **Geographic & State Breakdowns:** State-level hiring concentrations (led by Karnataka, Delhi, and Telangana).
- **Skill Co-occurrence Network:** Table of top pairwise technical synergies (`Machine Learning + Python` at 34.47%, `Django + Python` at 11.64%, `Flask + Python` at 11.56%).
- **Interactive Postings Explorer:** Searchable DataFrame displaying matching job records.

### Page 3: Salary Analytics (`dashboard/pages/salary_analytics.py`)
- **Integrity Guarantee:** Operates strictly on `cleaned_salary_model_data.csv` (**17,559 records**). Excludes invalid, missing, zero, or inverted salary rows.
- **Metric Consistency:** All compensation figures expressed in **INR Lakhs Per Annum (LPA)**.
- **Key Visualizations:**
  - Median Salary by Canonical Role: Ranked from `AI Engineer` (15.08 LPA) to `Data Analyst` (6.72 LPA).
  - Seniority Tier Progression: Multi-group box plots and statistical quartile spread table across `Fresher` (4.85 LPA median), `Junior` (7.48 LPA), `Mid-level` (12.25 LPA), `Senior` (18.70 LPA), and `Lead` (26.40 LPA).
  - Geographic Variations: Median compensation across top tech hubs.
  - Overall Salary Distribution Curve: Right-skewed continuous histogram.

### Page 4: Salary Prediction Engine (`dashboard/pages/salary_prediction.py`)
- **Integrated Model:** Tuned XGBoost Regressor with `log1p(y)` target transformation (`models/best_salary_model.joblib`).
- **Input Form:** Comprehensive inputs for Job Role, Experience (years), City, State, Work Mode, Employment Type, Education Level, Company Size, Industry, and Technical Skills multi-select.
- **Inference Diagnostics:**
  - Predicted Point Estimate in LPA and INR (e.g. `₹14.25 LPA` ≈ `₹14,25,000 / yr`).
  - Empirical 90% Confidence Interval: Lower Bound to Upper Bound ($\pm 1.645 \times \text{residual\_std}$).
  - Model metadata badge: Version `1.0.0`, test residual standard deviation `±4.53 LPA`.
  - Prominent non-guaranteed compensation disclaimer.

### Page 5: Resume Analyzer (`dashboard/pages/resume_analyzer.py`)
- **Integrated Parser:** PyMuPDF (`fitz`) engine via `src/resume_parser.py`.
- **Privacy Assurance:** Resumes are ingested strictly in-memory as byte buffers. Zero files, PII, names, or contact details are written to disk.
- **Document Validation:** Verifies `.pdf` extension, caps file size at 10 MB, and detects scanned/image-only PDFs.
- **Section & Skill Extraction:** Detects 5 standard sections (`skills`, `experience`, `projects`, `education`, `certifications`) and highlights matching technical skills as badge pills.
- **Workflow Bridge:** Includes button to transfer detected skills directly into the Skill Gap Analysis module via `st.session_state`.

### Page 6: Skill Gap Analysis (`dashboard/pages/skill_gap.py`)
- **Integrated Engine:** `src/skill_analyzer.py`.
- **Features:** Target role selection, candidate skill input (manual or imported from Resume Analyzer).
- **Match Score Formula:** Evaluates demand-weighted alignment:
  $$\text{Match Score} = \left( \frac{\sum_{s \in \text{Candidate} \cap \text{Role}} \text{Demand}(s)}{\sum_{s \in \text{Role}} \text{Demand}(s)} \right) \times 100$$
- **Visual Diagnostics:** Circular match percentage gauge, matched skill badges, missing Essential badges (demand $\ge 50\%$), and missing Important badges ($25\% \le \text{demand} < 50\%$).
- **Personalized Learning Pathways:** Structured recommendation cards detailing specific learning actions and practical portfolio projects for each missing competency.

### Page 7: Data Quality Report (`dashboard/pages/data_quality.py`)
- **Audit Funnel:**
  - Raw Records: **31,150**
  - Exact Duplicates Purged: **900**
  - Cleaned Job Market Dataset: **30,250**
  - Missing Salary Disclosures (Preserved for EDA): **12,145**
  - Initial Salary Records: **18,105**
  - Outliers / Inverted Bounds Purged: **546**
  - Final Verified Salary Modeling Set: **17,559**
- **Column Normalization Table:** Detailed protocol for role mapping, city/state resolution, work mode encoding, and skill standardization.
- **Transformed Feature Specifications:** 113-dimension encoded feature space details.

### Page 8: About & Methodology (`dashboard/pages/about.py`)
- Project scope, technology stack, data science architecture, and 5-model evaluation overview.
- Privacy principles: Zero PII storage, uncertainty intervals, fair demand weighting.
- Prominent Academic Scope & Simulated Dataset Disclosure.

---

## 3. UI Design System & Styling Details

The UI adheres strictly to modern SaaS styling guidelines:
- **Base Background:** `#0B1020` (Dark Navy)
- **Card Surfaces:** `#151D30` with subtle border `#1E293B`
- **Primary Accent:** `#3B82F6` (Electric Blue)
- **Secondary Accent:** `#8B5CF6` (Violet)
- **Text Palette:** Headers in `#F8FAFC`, secondary descriptions in `#94A3B8`, captions in `#64748B`
- **Custom CSS:** Injected via `dashboard/assets/style.css` without breaking core Streamlit components.
- **Visual Polish:** Responsive cards, custom metric badges, color-coded priority pills, and Plotly templates with seamless dark paper backgrounds.

---

## 4. Performance, Caching & Data-Source Handling

1. **Centralized Data Loader (`dashboard/data_loader.py`):**
   - `@st.cache_data`: Datasets (`cleaned_job_market_all.csv` and `cleaned_salary_model_data.csv`) and analytical summary dictionaries are cached in memory after the first read. Page navigation causes zero file re-reads.
   - `@st.cache_resource`: `SalaryPredictor` and `ResumeParser` instances are initialized once and preserved across sessions.
2. **Data-Source Transparency:**
   - The sidebar monitors system health via `get_system_health()`.
   - The database status clearly discloses **SQLite (Local Fallback Active)** due to the local PostgreSQL authentication blocker, ensuring complete transparency without inventing fake connections.
   - The service engine displays whether FastAPI or the high-throughput in-process engine is handling requests.

---

## 5. Automated Verification & Test Results

An automated test suite was constructed inside [`tests/test_dashboard.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/tests/test_dashboard.py):

```powershell
pytest -v
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-8.4.2
rootdir: c:\Users\LENOVO\OneDrive\Desktop\Applet logic\Data Science\india_job_market_internship_dataset\project_anti
collected 86 items

tests/test_api.py (9 passed)
tests/test_dashboard.py (10 passed)
tests/test_database.py (6 passed)
tests/test_feature_engineering.py (3 passed)
tests/test_job_market_intelligence.py (8 passed)
tests/test_preprocessing.py (9 passed)
tests/test_resume_parser.py (15 passed)
tests/test_salary_model.py (10 passed)
tests/test_skill_analyzer.py (16 passed)

============================= 86 passed in 11.62s =============================
```

- **Total Tests Passed:** **86 / 86 (100% pass rate)**
- **Dashboard Tests:** 10 passed (Imports, Data Loaders, Model Resources, System Health, Salary Prediction, Skill Gap Analysis, In-Memory Resume Parsing, Chart Generators, Edge Cases).
- **Regressions:** 0 regressions across all previous Step 1–8 modules.

---

## 6. Application Launch Verification

The application was tested and verified for live startup:
```powershell
streamlit run dashboard/app.py
```
- **Local URL:** `http://localhost:8501`
- **Health Check Endpoint:** `http://localhost:8501/_stcore/health` responded with HTTP `200 OK` (`ok`).
- **Startup Time:** Under 2 seconds with immediate rendering of the dark SaaS layout.

---

## 7. Known Technical Limitations & Responsible AI Scope

1. **Local PostgreSQL Service Configuration:**
   - The background Windows PostgreSQL service on port 5432 has custom password credentials.
   - The application gracefully operates on SQLite (`data/job_market.db`) with full ORM compatibility, as clearly disclosed on the UI sidebar and health checks.
2. **Synthetic Dataset Scope:**
   - The underlying 30,250 records represent simulated data. All figures and model outputs are educational benchmarks demonstrating an end-to-end data science architecture.

---

### Step 9 Completion Confirmation

**Step 9 (Module 6: Premium Interactive Streamlit Dashboard) is 100% implemented, tested, verified, and ready for deployment.**

