INDIA JOB MARKET DATASET — DATA DICTIONARY
================================================
File: india_job_market_messy_31150_records.csv
Rows: 31,150 (includes deliberately injected duplicate and near-duplicate records)
Columns: 19

IMPORTANT:
This is a SYNTHETIC dataset created for internship practice. It is not real job-market data.
Company names, job IDs, job descriptions, URLs and salary values are simulated.
Do not use it to make real career or salary decisions or claim it represents the Indian job market.

COLUMN DEFINITIONS
------------------
job_id              Synthetic job posting identifier
job_title           Job role
company_name        Simulated company name
city                City
state               Indian state/region
experience_level    Fresher / Junior / Mid-level / Senior / Lead (with intentional inconsistent labels)
experience_years    Numeric experience years
education           Education category
employment_type     Employment type
work_mode           On-site / Hybrid / Remote (with intentional inconsistent labels)
salary_min_lpa      Lower salary bound in INR lakh per annum
salary_max_lpa      Upper salary bound in INR lakh per annum
salary_currency     Currency (INR)
skills_required     Comma-separated skills
job_description     Simulated job description
company_size        Company size category
industry            Industry category
posted_date         Posting date (YYYY-MM-DD)
data_source         Simulated source category
job_url             Placeholder URL; not a real job link

INTENTIONAL DATA QUALITY ISSUES
-------------------------------
1. Missing values in multiple columns, including salary, company, city, skills and education.
2. Exact duplicate rows (approximately 900 rows added).
3. Near-duplicate job postings with changed IDs/URLs and some formatting differences.
4. Inconsistent categorical values (case, leading/trailing spaces, alternate labels).
5. Invalid salary values (negative minimum salaries and some maximum values below minimum).
6. Implausible experience values (negative values and extreme values).
7. Salary outliers and skewed distributions.
8. Uneven category frequencies and missingness patterns.

SUGGESTED EDA TASKS
-------------------
- Dataset shape, dtypes, describe(), missing-value count and percentage.
- Exact duplicate count and near-duplicate investigation.
- Salary distribution, boxplots, outlier analysis.
- Job-role, city, experience, work-mode and employment-type counts.
- Top skills extraction from skills_required.
- Salary by role, city and experience.
- Missingness heatmap and correlation analysis.
- Posting-date trend analysis.

SUGGESTED CLEANING TASKS
------------------------
- Standardize column names and categorical labels.
- Normalize city aliases (e.g. BANGALORE / bengaluru).
- Handle missing values with a documented strategy.
- Remove exact duplicates and investigate near duplicates.
- Validate salary_min_lpa <= salary_max_lpa and remove/correct invalid values.
- Investigate implausible experience_years.
- Parse posted_date and validate ranges.
- Document every cleaning decision; do not silently delete data.

For the salary prediction exercise:
- Create a clearly documented target, such as salary_mid_lpa = (salary_min_lpa + salary_max_lpa) / 2.
- Train only on rows with valid salary targets.
- Exclude identifiers, URLs and leakage-prone text fields from the initial baseline.
- Use a train/test split and fit preprocessing only on training data.
- Report MAE, RMSE and R2; inspect errors by role and city.
