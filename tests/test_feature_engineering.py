"""
Unit tests for feature engineering pipeline (src/feature_engineering.py).
"""

import numpy as np
import pandas as pd
import pytest

from src.feature_engineering import (
    LEAKAGE_COLUMNS,
    SkillsBinarizer,
    build_feature_pipeline,
    prepare_features_and_target,
    split_dataset,
)


def test_skills_binarizer():
    data = pd.Series([
        "Python, SQL, Machine Learning",
        "Python, AWS, Docker",
        "Java, SQL, Docker",
        "Python, Docker, Kubernetes",
    ])
    binarizer = SkillsBinarizer(top_n=3)
    binarizer.fit(data)

    # Top skills should be Python and Docker
    assert "Python" in binarizer.top_skills_
    assert "Docker" in binarizer.top_skills_
    assert len(binarizer.top_skills_) == 3

    # Transform test
    test_data = pd.Series(["Python, GCP", "Docker", np.nan])
    transformed = binarizer.transform(test_data)
    assert transformed.shape == (3, 3)

    # First row has Python (1), Docker (0)
    py_idx = binarizer.top_skills_.index("Python")
    assert transformed[0, py_idx] == 1.0

    # Feature names
    names = binarizer.get_feature_names_out()
    assert len(names) == 3
    assert all(n.startswith("skill_") for n in names)


def test_no_data_leakage_in_predictors():
    sample_df = pd.DataFrame({
        "job_title": ["Data Scientist", "Software Engineer"],
        "city": ["Bengaluru", "Hyderabad"],
        "state": ["Karnataka", "Telangana"],
        "experience_level": ["Mid-level", "Senior"],
        "experience_years": [4.0, 8.0],
        "work_mode": ["Hybrid", "Remote"],
        "employment_type": ["Full-time", "Full-time"],
        "education": ["Master's", "Bachelor's"],
        "company_size": ["201-500", "1000+"],
        "industry": ["FinTech", "Product"],
        "skills_required_clean": ["Python, SQL", "Java, AWS"],
        "skill_count": [2, 2],
        # Leakage columns
        "salary_min_lpa": [10.0, 15.0],
        "salary_max_lpa": [14.0, 20.0],
        "salary_mid_lpa": [12.0, 17.5],
        "salary_annual_inr": [1200000.0, 1750000.0],
        "is_salary_valid": [True, True],
    })

    X, y = prepare_features_and_target(sample_df)

    # Target check
    assert (y == sample_df["salary_mid_lpa"]).all()

    # Zero leakage check: none of the leakage columns must be in X
    for col in LEAKAGE_COLUMNS:
        assert col not in X.columns, f"Leakage detected: {col} is in predictors X!"


def test_pipeline_fit_transform_flow():
    sample_df = pd.DataFrame({
        "job_title": ["Data Scientist", "Software Engineer", "BI Developer", "Cloud Engineer", "MLOps Engineer"],
        "city": ["Bengaluru", "Hyderabad", "Pune", "Mumbai", "Delhi NCR"],
        "state": ["Karnataka", "Telangana", "Maharashtra", "Maharashtra", "Delhi"],
        "experience_level": ["Mid-level", "Senior", "Junior", "Lead", "Mid-level"],
        "experience_years": [4.0, 8.0, 2.0, 14.0, 5.0],
        "work_mode": ["Hybrid", "Remote", "On-site", "Hybrid", "Remote"],
        "employment_type": ["Full-time", "Full-time", "Contract", "Full-time", "Full-time"],
        "education": ["Master's", "Bachelor's", "Bachelor's", "PhD", "Master's"],
        "company_size": ["201-500", "1000+", "51-200", "1000+", "501-1000"],
        "industry": ["FinTech", "Product", "Telecom", "Cloud", "Healthcare Tech"],
        "skills_required_clean": [
            "Python, SQL, Machine Learning",
            "Java, AWS, Docker",
            "Power BI, SQL, Excel",
            "AWS, Kubernetes, Docker, Linux",
            "Python, Docker, Kubernetes, MLOps"
        ],
        "skill_count": [3, 3, 3, 4, 4],
        "salary_min_lpa": [10.0, 15.0, 6.0, 18.0, 12.0],
        "salary_max_lpa": [14.0, 20.0, 8.0, 24.0, 16.0],
        "salary_mid_lpa": [12.0, 17.5, 7.0, 21.0, 14.0],
        "salary_annual_inr": [1200000.0, 1750000.0, 700000.0, 2100000.0, 1400000.0],
        "is_salary_valid": [True, True, True, True, True],
    })

    X, y = prepare_features_and_target(sample_df)
    X_train, X_test, y_train, y_test = split_dataset(X, y, test_size=0.4, random_state=42)

    assert len(X_train) == 3
    assert len(X_test) == 2

    pipeline = build_feature_pipeline(top_n_skills=5)

    # Fit ONLY on training data
    pipeline.fit(X_train)

    # Transform both splits
    X_train_trans = pipeline.transform(X_train)
    X_test_trans = pipeline.transform(X_test)

    # Zero missing values in transformed output
    assert not np.isnan(X_train_trans).any()
    assert not np.isnan(X_test_trans).any()
    assert X_train_trans.shape[1] == X_test_trans.shape[1]

