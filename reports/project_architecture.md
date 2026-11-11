# Project System Architecture & Data Flow
## AI-Powered Job Market Intelligence & Salary Prediction System

**Document Version:** 1.0.0  
**Status:** Completed & Validated  

---

## 1. System Architecture Overview

The **AI-Powered Job Market Intelligence & Salary Prediction System** is structured as an enterprise-grade multi-tier Data Science application. The architecture cleanly decouples machine learning inference, natural language document processing, relational persistence, RESTful API delivery, and modern SaaS user interfaces.

```mermaid
flowchart TD
    subgraph Data_Layer ["Data Tier & Persistence"]
        Raw["Raw Data (31,150 CSV)"] --> Prep["Preprocessing Pipeline"]
        Prep --> CleanAll["cleaned_job_market_all.csv (30,250 rows)"]
        Prep --> CleanSal["cleaned_salary_model_data.csv (17,559 rows)"]
        CleanAll --> Ingest["Batch Ingestion Pipeline (load_data.py)"]
        Ingest --> DB[("Relational DB: SQLite / PostgreSQL")]
    end

    subgraph ML_Layer ["Machine Learning & Feature Pipeline"]
        CleanSal --> Split["80/20 Train-Test Split"]
        Split --> FT["113-Feature ColumnTransformer"]
        FT --> ModelTrain["Tuned XGBoost Regressor (log1p)"]
        ModelTrain --> ModelStore["Saved Artifacts (.joblib & .json)"]
    end

    subgraph Service_Tier ["Analytical & NLP Service Engines"]
        CleanAll --> JMI["Job Market Intelligence Engine (src/job_market_intelligence.py)"]
        DB --> JMI
        ModelStore --> SPE["Salary Prediction Engine (src/salary_model.py)"]
        PDF["Candidate Resume (PDF)"] --> RPE["In-Memory Resume Parser (src/resume_parser.py)"]
        RPE --> SGA["Skill Gap Analysis Engine (src/skill_analyzer.py)"]
        CleanAll --> SGA
    end

    subgraph Interface_Tier ["Presentation & API Layer"]
        JMI --> API["FastAPI REST Microservice (api/main.py)"]
        SPE --> API
        JMI --> Streamlit["Streamlit SaaS Dashboard (dashboard/app.py)"]
        SPE --> Streamlit
        RPE --> Streamlit
        SGA --> Streamlit
    end
```

---

## 2. End-to-End Data Flow

1. **Ingestion & Preprocessing:**
   - The uncleaned dataset (`india_job_market_messy_31150_records.csv`) contains 31,150 rows.
   - Exact deduplication eliminates 900 rows, yielding 30,250 unique records.
   - Text fields are stripped and normalized; job titles are mapped via `ROLE_NORMALIZATION_MAP` into 12 canonical roles.
   - Missing salary disclosures (12,145 postings) are preserved for overall market demand analytics, while high-integrity rows (17,559 records) are filtered into the salary modeling set.
2. **Feature Engineering & Transformation:**
   - Numerical features (`experience_years`, `skill_count`) are transformed via `RobustScaler`.
   - Categorical features (`job_title`, `city`, `state`, `experience_level`, `work_mode`, `employment_type`, `education`, `company_size`, `industry`) are one-hot encoded with `handle_unknown='ignore'`.
   - Technical skills are multi-hot encoded using a `MultiLabelBinarizer` covering the top 25 canonical market skills.
   - Total transformed feature dimensionality is **113 features**.
3. **Model Inference:**
   - Point estimates are predicted using the champion Tuned XGBoost Regressor fitted on `log1p(salary_mid_lpa)`:
     $$\hat{y} = \exp\left( f_{\text{XGB}}(x) \right) - 1$$
   - Prediction intervals are derived from empirical test residuals ($s_{\text{resid}} = 4.53\text{ LPA}$):
     $$\text{CI}_{90\%} = \left[ \hat{y} - 1.645 \cdot s_{\text{resid}}, \; \hat{y} + 1.645 \cdot s_{\text{resid}} \right]$$

---

## 3. Natural Language Processing & Resume Parsing Workflow

```mermaid
flowchart LR
    Upload["PDF Upload (Bytes Stream)"] --> Val["Validation: Type, Size <= 10MB"]
    Val --> InMem["In-Memory Fitz (PyMuPDF) Ingestion"]
    InMem --> Heuristic["Selectable Text Check (>50 chars)"]
    Heuristic -- Yes --> TextClean["Text Normalization & Line Preservation"]
    Heuristic -- No / Scanned --> Warn["OCR Limitation Warning"]
    TextClean --> SecExtract["Section Segmentation: Skills, Experience, Education"]
    TextClean --> RegexMap["Word-Boundary Regex Skill Taxonomy (42 Skills)"]
    RegexMap --> Normalize["Alias Normalization (e.g. py -> Python)"]
    Normalize --> Unique["Deduplicated Canonical Skill Set"]
    Unique --> Session["Forward to Skill Gap Analyzer (st.session_state)"]
```

---

## 4. Skill Gap Analysis & Recommendation Architecture

```mermaid
flowchart TD
    TargetRole["Target Job Role Selection"] --> RoleQuery["Query Cleaned Dataset for Role Postings"]
    RoleQuery --> Benchmarks["Compute Empirical Skill Demand (%)"]
    Benchmarks --> Classify["Threshold Classification: Essential (>=50%), Important (25-50%), Additional (<25%)"]
    
    CandSkills["Candidate Skills (Resume / Input)"] --> MatchEngine["Demand-Weighted Scoring Engine"]
    Classify --> MatchEngine
    
    MatchEngine --> Score["Formula: (Matched Demand / Total Role Demand) * 100"]
    MatchEngine --> GapReport["Missing Skills Breakdown by Priority Tier"]
    GapReport --> Guidance["Personalized Learning Guidance & Portfolio Practice"]
```

---

## 5. Relational Database Entity-Relationship Diagram

```mermaid
erDiagram
    COMPANIES ||--o{ JOB_POSTINGS : "employs"
    JOB_POSTINGS ||--o{ JOB_SKILLS : "requires"
    SKILLS ||--o{ JOB_SKILLS : "associated_with"

    COMPANIES {
        int id PK
        string name UK "Indexed"
        datetime created_at
    }

    SKILLS {
        int id PK
        string name UK "Indexed"
        string category
        datetime created_at
    }

    JOB_POSTINGS {
        int id PK
        string job_id UK "Indexed"
        string job_title "Indexed"
        string clean_role "Indexed"
        int company_id FK
        string city "Indexed"
        string state
        string experience_level "Indexed"
        float experience_years
        string education
        string employment_type
        string work_mode "Indexed"
        float salary_min_lpa
        float salary_max_lpa
        float salary_mid_lpa "Indexed"
        bigint salary_annual_inr
        boolean is_salary_valid "Indexed"
        string company_size
        string industry
        string posted_date
        int posted_year
        int posted_month
        datetime created_at
    }

    JOB_SKILLS {
        int id PK
        int job_posting_id FK "Indexed"
        int skill_id FK "Indexed"
    }
```

---

## 6. Service Integration & Resilience

1. **Dual Service Delivery:**
   - **Interactive Frontend:** Streamlit (`dashboard/app.py`) provides human-interactive exploration, forms, file uploads, and Plotly charts.
   - **REST Microservice:** FastAPI (`api/main.py`) exposes JSON endpoints for programmatic integration.
2. **Database Fallback:**
   - Both interfaces connect through `database/db.py`.
   - If PostgreSQL credentials fail or the server is unavailable, the system automatically runs on local SQLite (`sqlite:///./data/job_market.db`).
   - The active database engine is disclosed on the Streamlit sidebar and API `/health` endpoint.
3. **Memory Caching:**
   - Streamlit utilizes `@st.cache_data` for heavy DataFrame aggregations and `@st.cache_resource` for initialized machine learning predictors and NLP parsers, preventing redundant computations.

