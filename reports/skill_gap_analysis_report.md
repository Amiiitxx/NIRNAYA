# Module 4: Skill Gap Analysis & Recommendation Engine Report
## AI-Powered Job Market Intelligence & Salary Prediction System

**Document Version:** 1.0.0  
**Status:** Completed & Validated  
**Module Implementation:** [`src/skill_analyzer.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/src/skill_analyzer.py)  
**Notebook Execution:** [`notebooks/07_skill_gap_analysis.ipynb`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/notebooks/07_skill_gap_analysis.ipynb)  
**Unit Test Suite:** [`tests/test_skill_analyzer.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/tests/test_skill_analyzer.py) (16 tests passing, total project suite: **53/53 passing**)  
**Dataset Reference:** `data/processed/cleaned_job_market_all.csv` (30,250 records across 12 canonical tech roles)  

> **Educational & Dataset Scope Disclaimer:** The analytical findings, skill distributions, and demand metrics documented herein represent the supplied project dataset (`cleaned_job_market_all.csv`), which contains structured synthetic and simulated job market data for engineering development. They reflect realistic Indian tech hiring patterns for educational and benchmark purposes, but must not be cited as real-time census or live Indian labor market statistics.

---

## 1. Implementation Overview

Module 4 delivers a transparent, mathematically grounded Skill Gap Analysis and Personalized Learning Recommendation Engine. It bridges candidate resume profiles with empirical market requirements across 12 canonical Indian tech job roles.

### Key Architectural Capabilities:
1. **Empirical Market Demand Profiling (`analyze_market_skill_demand`):** Evaluates frequency and market demand percentage across all 30,250 job postings. Handles multi-skill postings with strict set deduplication so that duplicate mentions within a single posting are counted exactly once.
2. **Dynamic Canonical Role Benchmarking (`get_role_required_skills`):** Dynamically filters postings by job title and calculates role-specific skill demand distributions across three project-defined priority tiers:
   - **Essential Skills:** Demand $\ge 50.0\%$ (Foundational core competencies).
   - **Important Skills:** Demand $\ge 25.0\%$ and $< 50.0\%$ (High-value complementary tools).
   - **Additional Skills:** Demand $< 25.0\%$ (Niche or specialized technologies).
3. **Demand-Weighted Skill Match Scoring (`calculate_skill_match_score`):** Matches candidate skills against role requirements using empirical demand percentages as weights, ensuring that missing high-demand core competencies impact the score far more than missing secondary tools.
4. **Actionable Learning Pathways (`generate_learning_recommendations`):** Generates structured, practical learning actions and hands-on portfolio project practice assignments prioritized by skill criticality.

---

## 2. Dataset Source & Row Coverage

The analysis operates on the complete cleaned dataset:
- **File:** `data/processed/cleaned_job_market_all.csv`
- **Total Valid Postings:** **30,250 rows $\times$ 29 columns**
- **Canonical Tech Job Roles (12 Total):**
  1. `Business Analyst`: 2,604 postings (8.61%)
  2. `BI Developer`: 2,586 postings (8.55%)
  3. `Cloud Engineer`: 2,562 postings (8.47%)
  4. `Data Engineer`: 2,542 postings (8.40%)
  5. `Software Engineer`: 2,528 postings (8.36%)
  6. `Python Developer`: 2,505 postings (8.28%)
  7. `MLOps Engineer`: 2,500 postings (8.26%)
  8. `Data Scientist`: 2,497 postings (8.25%)
  9. `NLP Engineer`: 2,489 postings (8.23%)
  10. `Machine Learning Engineer`: 2,487 postings (8.22%)
  11. `Data Analyst`: 2,480 postings (8.20%)
  12. `AI Engineer`: 2,470 postings (8.17%)

---

## 3. Skill Normalization & Demand Calculation Methodology

### Deduplication per Job Posting:
Raw postings frequently contain repetitive skill mentions (e.g. `"Python, SQL, Machine Learning, Python"`). The engine applies per-row tokenization into a unique Python `set()` before aggregation:

$$\text{Posting Skills}_i = \left\{ \text{strip}(s) \mid s \in \text{split}(\text{row}_i[\text{skills\_required\_clean}], \text{','}) \right\}$$

$$\text{Skill Job Count}(s) = \sum_{i=1}^{N_{\text{postings}}} \mathbb{I}\left( s \in \text{Posting Skills}_i \right)$$

$$\text{Demand Percentage}(s) = \left( \frac{\text{Skill Job Count}(s)}{N_{\text{postings}}} \right) \times 100$$

### Top 15 Technical Skills Across Entire Job Market:
| Rank | Technical Skill | Total Postings | Market Demand Percentage |
| :---: | :--- | :---: | :---: |
| 1 | `Python` | 10,439 | 34.51% |
| 2 | `Machine Learning` | 10,426 | 34.47% |
| 3 | `Django` | 5,050 | 16.69% |
| 4 | `Pandas` | 5,015 | 16.58% |
| 5 | `Git` | 4,991 | 16.50% |
| 6 | `Flask` | 4,990 | 16.50% |
| 7 | `Azure` | 4,980 | 16.46% |
| 8 | `dbt` | 4,958 | 16.39% |
| 9 | `Computer Vision` | 4,947 | 16.35% |
| 10 | `Scikit-learn` | 4,943 | 16.34% |
| 11 | `React` | 4,937 | 16.32% |
| 12 | `SQL` | 4,923 | 16.27% |
| 13 | `Tableau` | 4,921 | 16.27% |
| 14 | `FastAPI` | 4,917 | 16.25% |
| 15 | `Docker` | 4,909 | 16.23% |

![Top 20 Market Skills](figures/market_skill_demand_top20.png)

---

## 4. Role-Specific Skill Requirements Analysis

When filtered by target role, technical requirements exhibit distinct specialization profiles:

### 1. Data Scientist ($N = 2,497$ postings):
- **Essential ($\ge 50\%$):**
  - `Machine Learning`: 1,786 postings (**71.53%**)
  - `Python`: 1,776 postings (**71.13%**)
- **Additional ($< 25\%$):**
  - `Django`: 466 postings (18.66%)
  - `Pandas`: 442 postings (17.70%)
  - `Docker`: 424 postings (16.98%)
  - `SQL`: 423 postings (16.94%)
  - `Git`: 417 postings (16.70%)
  - `NumPy`: 414 postings (16.58%)
  - `AWS`: 413 postings (16.54%)

### 2. Machine Learning Engineer ($N = 2,487$ postings):
- **Essential ($\ge 50\%$):**
  - `Machine Learning`: 1,765 postings (**71.01%**)
  - `Python`: 1,762 postings (**70.85%**)
- **Additional ($< 25\%$):**
  - `Hadoop`: 441 postings (17.73%)
  - `Git`: 439 postings (17.65%)
  - `SQL`: 423 postings (17.01%)
  - `Computer Vision`: 423 postings (17.01%)
  - `Pandas`: 419 postings (16.85%)
  - `Power BI`: 419 postings (16.85%)

### 3. Software Engineer ($N = 2,528$ postings):
- **Additional ($< 25\%$):**
  - `Docker`: 452 postings (17.88%)
  - `Airflow`: 445 postings (17.60%)
  - `Scikit-learn`: 441 postings (17.44%)
  - `Statistics`: 441 postings (17.44%)
  - `NLP`: 439 postings (17.37%)
  - `FastAPI`: 433 postings (17.13%)
  - `NumPy`: 432 postings (17.09%)

---

## 5. Demand-Weighted Skill Match Score Formula

Rather than treating all skills equally (where missing a niche library penalizes a candidate as much as missing Python), the match score is weighted by the empirical demand percentage of each skill in that role:

$$\text{Skill Match Score} = \left( \frac{\sum_{s \in \text{Matched Skills}} \text{Demand Percentage}(s)}{\sum_{s \in \text{All Required Skills}} \text{Demand Percentage}(s)} \right) \times 100$$

### Mathematical Properties:
1. **Range:** Bound between $0.0\%$ (zero matched skills) and $100.0\%$ (all role skills matched).
2. **Prioritization Sensitivity:** Possessing `Python` ($71.13\%$) and `Machine Learning` ($71.53\%$) contributes $142.66$ weight units, immediately elevating the match score substantially more than acquiring secondary tools.
3. **Empty Input Safety:** If no skills are extracted from the candidate's resume or the role is unobserved, the score returns $0.0\%$ with a diagnostic warning.

---

## 6. Example Candidate Skill Gap Analysis

### Candidate Profile:
- **Current Extracted Skills:** `['Excel', 'Git', 'NumPy', 'Pandas', 'Power BI', 'Python', 'SQL']`
- **Target Role:** `Data Scientist`

### Evaluation Results:
- **Total Skills Evaluated for Role:** 32 skills
- **Skill Match Score:** **30.34%**
- **Matched Skills (7):** `['Python', 'SQL', 'Pandas', 'Git', 'NumPy', 'Excel', 'Power BI']`
- **Essential Skills Status:**
  - `Python`: **Matched** (71.13% demand)
  - `Machine Learning`: **Missing Gap** (71.53% demand) $\rightarrow$ **Critical Essential Gap**
- **Important Skills Missing:** None (no skills in 25–50% band for this role).
- **Additional Skills Missing (24):** `['Machine Learning', 'Django', 'Docker', 'JavaScript', 'AWS', 'GCP', 'Linux', 'Tableau', 'FastAPI', 'Deep Learning', ...]`

![Skill Gap Match Comparison](figures/skill_gap_match_comparison.png)

---

## 7. Personalized Learning Recommendation Logic

Missing skills are sorted first by priority category (`Essential` $\rightarrow$ `Important` $\rightarrow$ `Additional`), then descending by market demand percentage.

### Sample Actionable Recommendations for Candidate:
1. **Machine Learning** (`Essential` — **71.5% Market Demand**):
   - *Suggested Learning Action:* Study supervised and unsupervised algorithms, cross-validation, and metric evaluation with Scikit-learn.
   - *Suggested Project Practice:* Build and tune an end-to-end regression/classification pipeline with cross-validated hyperparameter search.
2. **Django** (`Additional` — **18.7% Market Demand**):
   - *Suggested Learning Action:* Learn Django ORM, authentication system, class-based views, and Django REST Framework (DRF).
   - *Suggested Project Practice:* Create a full-featured web app with relational models, user authentication, and admin dashboard.
3. **Docker** (`Additional` — **17.0% Market Demand**):
   - *Suggested Learning Action:* Master containerization, multi-stage Dockerfiles, image caching, and volume mapping.
   - *Suggested Project Practice:* Containerize a multi-service web application (FastAPI + PostgreSQL + Redis) using Docker Compose.
4. **AWS** (`Additional` — **16.5% Market Demand**):
   - *Suggested Learning Action:* Study core AWS services: EC2, S3, Lambda, IAM policies, and VPC networking fundamentals.
   - *Suggested Project Practice:* Deploy a serverless data ingestion pipeline triggered by S3 uploads using AWS Lambda and CloudWatch.

---

## 8. Unit Test Suite Results

The dedicated test suite [`tests/test_skill_analyzer.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/tests/test_skill_analyzer.py) validates all 16 specification points:

```powershell
pytest tests/test_skill_analyzer.py -v
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-8.4.2
collected 16 items

tests/test_skill_analyzer.py::test_get_available_job_roles PASSED        [  6%]
tests/test_skill_analyzer.py::test_normalize_role_title PASSED           [ 12%]
tests/test_skill_analyzer.py::test_overall_market_skill_demand PASSED    [ 18%]
tests/test_skill_analyzer.py::test_grouped_market_skill_demand_by_role PASSED [ 25%]
tests/test_skill_analyzer.py::test_grouped_market_skill_demand_by_experience PASSED [ 31%]
tests/test_skill_analyzer.py::test_duplicate_skill_in_same_posting_handled PASSED [ 37%]
tests/test_skill_analyzer.py::test_role_skill_priority_classification PASSED [ 43%]
tests/test_skill_analyzer.py::test_demand_weighted_skill_match_score_formula PASSED [ 50%]
tests/test_skill_analyzer.py::test_match_score_boundary_conditions PASSED [ 56%]
tests/test_skill_analyzer.py::test_compare_candidate_skills PASSED       [ 62%]
tests/test_skill_analyzer.py::test_generate_learning_recommendations PASSED [ 68%]
tests/test_skill_analyzer.py::test_generate_skill_gap_report_schema PASSED [ 75%]
tests/test_skill_analyzer.py::test_invalid_job_role_fallback PASSED      [ 81%]
tests/test_skill_analyzer.py::test_empty_candidate_skills_warning PASSED [ 87%]
tests/test_skill_analyzer.py::test_integration_with_resume_extraction PASSED [ 93%]
tests/test_skill_analyzer.py::test_skill_gap_analyzer_class PASSED       [100%]

============================= 16 passed in 3.28s ==============================
```

**Full Project Verification:** All 53 tests across Modules 1, 2, 3, and 4 pass in 5.09 seconds.

---

## 9. Privacy, Security & Governance

1. **No Data Storage:** Skill gap analysis runs strictly in-memory. Extracted skill arrays and candidate profiles are evaluated and discarded immediately.
2. **Zero PII Exposure:** The analyzer operates exclusively on technical skill tokens (`List[str]`), completely divorced from candidate names, emails, addresses, or employers.
3. **Responsible Scoring Communication:** The skill match score is explicitly labeled as an alignment metric with historical job postings, avoiding any misleading claims of predictive hiring probability or employability guarantees.

