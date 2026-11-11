"""
Unit tests for data cleaning and preprocessing pipeline (src/preprocessing.py).
"""

import numpy as np
import pandas as pd
import pytest

from src.preprocessing import (
    CITY_NORMALIZATION_MAP,
    CITY_TO_STATE_MAP,
    JobMarketPreprocessor,
    clean_skills,
    clean_text_field,
    infer_experience_level,
    normalize_city,
    normalize_employment_type,
    normalize_experience_level,
    normalize_work_mode,
)


def test_clean_text_field():
    assert clean_text_field("  Software Engineer  ") == "Software Engineer"
    assert clean_text_field("Data   Scientist") == "Data Scientist"
    assert pd.isna(clean_text_field(np.nan))
    assert pd.isna(clean_text_field("   "))


def test_normalize_city():
    assert normalize_city("BANGALORE") == "Bengaluru"
    assert normalize_city(" bengaluru ") == "Bengaluru"
    assert normalize_city("HYDERABAD") == "Hyderabad"
    assert normalize_city("kochi") == "Kochi"
    assert normalize_city("Delhi NCR") == "Delhi NCR"
    assert pd.isna(normalize_city(np.nan))


def test_state_mapping():
    assert CITY_TO_STATE_MAP["Bengaluru"] == "Karnataka"
    assert CITY_TO_STATE_MAP["Hyderabad"] == "Telangana"
    assert CITY_TO_STATE_MAP["Pune"] == "Maharashtra"
    assert CITY_TO_STATE_MAP["Kochi"] == "Kerala"


def test_normalize_work_mode():
    assert normalize_work_mode("Hybrid ") == "Hybrid"
    assert normalize_work_mode("ON-SITE") == "On-site"
    assert normalize_work_mode("remote") == "Remote"
    assert pd.isna(normalize_work_mode(np.nan))


def test_normalize_experience_level():
    assert normalize_experience_level("junior") == "Junior"
    assert normalize_experience_level("SENIOR") == "Senior"
    assert normalize_experience_level("mid level") == "Mid-level"
    assert normalize_experience_level("Mid-level") == "Mid-level"
    assert pd.isna(normalize_experience_level(np.nan))


def test_normalize_employment_type():
    assert normalize_employment_type("full time") == "Full-time"
    assert normalize_employment_type("FULL-TIME") == "Full-time"
    assert normalize_employment_type("Contract ") == "Contract"
    assert normalize_employment_type("Internship") == "Internship"


def test_infer_experience_level():
    assert infer_experience_level(0.0) == "Fresher"
    assert infer_experience_level(1.0) == "Fresher"
    assert infer_experience_level(2.5) == "Junior"
    assert infer_experience_level(5.0) == "Mid-level"
    assert infer_experience_level(9.0) == "Senior"
    assert infer_experience_level(15.0) == "Lead"
    assert pd.isna(infer_experience_level(-2.0))
    assert pd.isna(infer_experience_level(np.nan))


def test_clean_skills():
    raw = " Python, k8s,  FastAPI, SQL, py, Kubernetes "
    clean_str, skill_list = clean_skills(raw)
    assert "Python" in skill_list
    assert "Kubernetes" in skill_list
    assert "FastAPI" in skill_list
    assert "SQL" in skill_list
    # Duplicate alias "py" should map to "Python" and not duplicate
    assert skill_list.count("Python") == 1
    assert skill_list.count("Kubernetes") == 1


def test_preprocessor_end_to_end_on_synthetic_batch():
    sample_data = pd.DataFrame([
        {
            "job_id": "J1",
            "job_title": " Data Scientist ",
            "company_name": "Tech Corp",
            "city": "BANGALORE",
            "state": np.nan,
            "experience_level": "junior",
            "experience_years": 2.0,
            "education": "Bachelor's",
            "employment_type": "full time",
            "work_mode": "Hybrid ",
            "salary_min_lpa": 8.0,
            "salary_max_lpa": 12.0,
            "salary_currency": "INR",
            "skills_required": "Python, SQL, ML",
            "job_description": "Great role",
            "company_size": "201-500",
            "industry": "IT Services",
            "posted_date": "2026-03-15",
            "data_source": "Portal A",
            "job_url": "http://example.com/1",
        },
        # Duplicate of J1
        {
            "job_id": "J1",
            "job_title": " Data Scientist ",
            "company_name": "Tech Corp",
            "city": "BANGALORE",
            "state": np.nan,
            "experience_level": "junior",
            "experience_years": 2.0,
            "education": "Bachelor's",
            "employment_type": "full time",
            "work_mode": "Hybrid ",
            "salary_min_lpa": 8.0,
            "salary_max_lpa": 12.0,
            "salary_currency": "INR",
            "skills_required": "Python, SQL, ML",
            "job_description": "Great role",
            "company_size": "201-500",
            "industry": "IT Services",
            "posted_date": "2026-03-15",
            "data_source": "Portal A",
            "job_url": "http://example.com/1",
        },
        # Invalid salary record (negative min)
        {
            "job_id": "J2",
            "job_title": "Data Analyst",
            "company_name": "Fin Corp",
            "city": "HYDERABAD",
            "state": np.nan,
            "experience_level": "mid level",
            "experience_years": -2.0,  # Negative experience
            "education": "Master's",
            "employment_type": "Contract ",
            "work_mode": "remote",
            "salary_min_lpa": -5.0,  # Negative salary
            "salary_max_lpa": 10.0,
            "salary_currency": "INR",
            "skills_required": "Excel, Power BI",
            "job_description": "Data analysis",
            "company_size": "51-200",
            "industry": "FinTech",
            "posted_date": "2026-04-10",
            "data_source": "Portal B",
            "job_url": "http://example.com/2",
        },
    ])

    preprocessor = JobMarketPreprocessor(raw_filepath="")
    cleaned_df = preprocessor.clean_dataset(sample_data)

    # 1. Deduplication check
    assert len(cleaned_df) == 2  # 1 duplicate removed

    # 2. City & State check
    j1 = cleaned_df[cleaned_df["job_id"] == "J1"].iloc[0]
    assert j1["city"] == "Bengaluru"
    assert j1["state"] == "Karnataka"  # Imputed from Bengaluru
    assert j1["work_mode"] == "Hybrid"
    assert j1["experience_level"] == "Junior"
    assert j1["employment_type"] == "Full-time"
    assert j1["is_salary_valid"] is True or j1["is_salary_valid"] == 1
    assert j1["salary_mid_lpa"] == 10.0
    assert j1["salary_annual_inr"] == 1000000.0

    # 3. Anomaly correction on J2
    j2 = cleaned_df[cleaned_df["job_id"] == "J2"].iloc[0]
    assert j2["city"] == "Hyderabad"
    assert j2["state"] == "Telangana"  # Imputed from Hyderabad
    assert j2["experience_level"] == "Mid-level"
    assert j2["experience_years"] == 4.0  # Imputed from Mid-level median
    assert j2["is_salary_valid"] is False or j2["is_salary_valid"] == 0
    assert pd.isna(j2["salary_mid_lpa"])

    # 4. Salary model extraction check
    salary_model_df = preprocessor.extract_salary_model_data(cleaned_df)
    assert len(salary_model_df) == 1
    assert salary_model_df.iloc[0]["job_title"] == "Data Scientist"
    assert "job_id" not in salary_model_df.columns

