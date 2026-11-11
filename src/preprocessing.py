"""
Module: Data Preprocessing
Description: Production-ready data cleaning and preprocessing pipeline for the Indian Job Market dataset.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# ---------------------------------------------------------
# CANONICAL MAPPINGS & STANDARDIZATION DICTIONARIES
# ---------------------------------------------------------

CITY_NORMALIZATION_MAP: Dict[str, str] = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "hyderabad": "Hyderabad",
    "delhi ncr": "Delhi NCR",
    "ahmedabad": "Ahmedabad",
    "coimbatore": "Coimbatore",
    "chennai": "Chennai",
    "kolkata": "Kolkata",
    "mumbai": "Mumbai",
    "indore": "Indore",
    "thiruvananthapuram": "Thiruvananthapuram",
    "pune": "Pune",
    "noida": "Noida",
    "kochi": "Kochi",
    "gurugram": "Gurugram",
    "jaipur": "Jaipur",
}

CITY_TO_STATE_MAP: Dict[str, str] = {
    "Bengaluru": "Karnataka",
    "Hyderabad": "Telangana",
    "Delhi NCR": "Delhi",
    "Ahmedabad": "Gujarat",
    "Coimbatore": "Tamil Nadu",
    "Chennai": "Tamil Nadu",
    "Kolkata": "West Bengal",
    "Mumbai": "Maharashtra",
    "Indore": "Madhya Pradesh",
    "Thiruvananthapuram": "Kerala",
    "Pune": "Maharashtra",
    "Noida": "Uttar Pradesh",
    "Kochi": "Kerala",
    "Gurugram": "Haryana",
    "Jaipur": "Rajasthan",
}

WORK_MODE_NORMALIZATION_MAP: Dict[str, str] = {
    "on-site": "On-site",
    "onsite": "On-site",
    "hybrid": "Hybrid",
    "remote": "Remote",
}

EXPERIENCE_LEVEL_NORMALIZATION_MAP: Dict[str, str] = {
    "fresher": "Fresher",
    "junior": "Junior",
    "mid-level": "Mid-level",
    "mid level": "Mid-level",
    "senior": "Senior",
    "lead": "Lead",
}

EMPLOYMENT_TYPE_NORMALIZATION_MAP: Dict[str, str] = {
    "full-time": "Full-time",
    "full time": "Full-time",
    "contract": "Contract",
    "internship": "Internship",
    "part-time": "Part-time",
    "part time": "Part-time",
}

SKILL_CANONICAL_MAP: Dict[str, str] = {
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "python": "Python",
    "py": "Python",
    "sql": "SQL",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "tableau": "Tableau",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "git": "Git",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "spark": "Spark",
    "hadoop": "Hadoop",
    "dbt": "dbt",
    "airflow": "Airflow",
    "linux": "Linux",
    "java": "Java",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "react": "React",
    "excel": "Excel",
}

EXPERIENCE_LEVEL_MEDIANS: Dict[str, float] = {
    "Fresher": 0.0,
    "Junior": 1.0,
    "Mid-level": 4.0,
    "Senior": 8.0,
    "Lead": 13.0,
}


# ---------------------------------------------------------
# CLEANING & TRANSFORMATION FUNCTIONS
# ---------------------------------------------------------

def clean_text_field(val: Optional[str]) -> Optional[str]:
    """Strip whitespace and collapse multiple spaces."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = re.sub(r"\s+", " ", s)
    return s if s else np.nan


def normalize_city(city_val: Optional[str]) -> Optional[str]:
    """Standardize city names and resolve common aliases/casing."""
    cleaned = clean_text_field(city_val)
    if pd.isna(cleaned):
        return np.nan
    key = cleaned.lower()
    return CITY_NORMALIZATION_MAP.get(key, cleaned.title())


def normalize_work_mode(mode_val: Optional[str]) -> Optional[str]:
    """Standardize work mode casing and whitespace."""
    cleaned = clean_text_field(mode_val)
    if pd.isna(cleaned):
        return np.nan
    key = cleaned.lower()
    return WORK_MODE_NORMALIZATION_MAP.get(key, cleaned.title())


def normalize_experience_level(exp_val: Optional[str]) -> Optional[str]:
    """Standardize experience level casing and formatting."""
    cleaned = clean_text_field(exp_val)
    if pd.isna(cleaned):
        return np.nan
    key = cleaned.lower()
    return EXPERIENCE_LEVEL_NORMALIZATION_MAP.get(key, cleaned.title())


def normalize_employment_type(emp_val: Optional[str]) -> Optional[str]:
    """Standardize employment type casing and formatting."""
    cleaned = clean_text_field(emp_val)
    if pd.isna(cleaned):
        return np.nan
    key = cleaned.lower()
    return EMPLOYMENT_TYPE_NORMALIZATION_MAP.get(key, cleaned.title())


def infer_experience_level(years: Optional[float]) -> Optional[str]:
    """Infer experience seniority category from numeric years."""
    if pd.isna(years) or years < 0:
        return np.nan
    if years <= 1.0:
        return "Fresher"
    elif years <= 3.0:
        return "Junior"
    elif years <= 7.0:
        return "Mid-level"
    elif years <= 12.0:
        return "Senior"
    else:
        return "Lead"


def clean_skills(skills_val: Optional[str]) -> Tuple[Optional[str], List[str]]:
    """
    Parse comma-separated skills string into a normalized canonical string
    and list of distinct skills.
    """
    if pd.isna(skills_val):
        return np.nan, []
    
    tokens = str(skills_val).split(",")
    canonical_list: List[str] = []
    seen = set()
    
    for t in tokens:
        stripped = t.strip()
        if not stripped:
            continue
        lower_t = stripped.lower()
        canon = SKILL_CANONICAL_MAP.get(lower_t, stripped)
        if canon.lower() not in seen:
            seen.add(canon.lower())
            canonical_list.append(canon)
            
    if not canonical_list:
        return np.nan, []
    
    return ", ".join(canonical_list), canonical_list


# ---------------------------------------------------------
# END-TO-END DATASET CLEANING PIPELINE
# ---------------------------------------------------------

class JobMarketPreprocessor:
    """
    Orchestrates end-to-end cleaning, anomaly detection, deduplication,
    and target variable engineering for the job market dataset.
    """

    def __init__(self, raw_filepath: str):
        self.raw_filepath = raw_filepath
        self.cleaning_report: Dict[str, any] = {}

    def load_data(self) -> pd.DataFrame:
        """Load raw CSV file from candidate paths."""
        candidate_paths = [
            self.raw_filepath,
            os.path.join("..", self.raw_filepath) if not self.raw_filepath.startswith("..") else self.raw_filepath,
            os.path.join("data", "raw", "india_job_market_messy_31150_records.csv"),
            os.path.join("..", "data", "raw", "india_job_market_messy_31150_records.csv"),
        ]
        target_path = next((p for p in candidate_paths if p and os.path.exists(p)), None)
        if not target_path:
            raise FileNotFoundError(f"Raw dataset not found in candidate paths: {candidate_paths}")
        return pd.read_csv(target_path)

    def clean_dataset(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Execute full data cleaning workflow.
        Returns cleaned DataFrame with all 30,250 unique records.
        """
        initial_rows = len(df_raw)
        df = df_raw.copy()

        # 1. Deduplication
        exact_dups = df.duplicated().sum()
        df = df.drop_duplicates().reset_index(drop=True)
        self.cleaning_report["exact_duplicates_removed"] = int(exact_dups)
        self.cleaning_report["post_dedup_rows"] = len(df)

        # 2. Text standardization & categorical harmonization
        df["job_title"] = df["job_title"].apply(clean_text_field)
        df["company_name"] = df["company_name"].apply(clean_text_field)
        df["city"] = df["city"].apply(normalize_city)
        df["work_mode"] = df["work_mode"].apply(normalize_work_mode)
        df["experience_level"] = df["experience_level"].apply(normalize_experience_level)
        df["employment_type"] = df["employment_type"].apply(normalize_employment_type)
        df["education"] = df["education"].apply(clean_text_field)
        df["company_size"] = df["company_size"].apply(clean_text_field)
        df["industry"] = df["industry"].apply(clean_text_field)

        # Impute missing state from known city
        df["state"] = df["state"].astype(object)
        imputed_states = 0
        for idx in df[df["state"].isna() & df["city"].notna()].index:
            c = df.loc[idx, "city"]
            if c in CITY_TO_STATE_MAP:
                df.loc[idx, "state"] = CITY_TO_STATE_MAP[c]
                imputed_states += 1
        self.cleaning_report["states_imputed_from_city"] = imputed_states

        # 3. Experience Anomaly Cleaning & Imputation
        # Flag negative and extreme (> 35) years
        invalid_exp_mask = (df["experience_years"] < 0) | (df["experience_years"] > 35)
        self.cleaning_report["invalid_experience_years_detected"] = int(invalid_exp_mask.sum())
        df.loc[invalid_exp_mask, "experience_years"] = np.nan

        # If experience_level is missing but experience_years is valid, infer level
        level_missing_mask = df["experience_level"].isna() & df["experience_years"].notna()
        df.loc[level_missing_mask, "experience_level"] = df.loc[level_missing_mask, "experience_years"].apply(infer_experience_level)

        # If experience_years is missing, impute from experience_level median
        years_missing_mask = df["experience_years"].isna()
        self.cleaning_report["missing_experience_years_before_imputation"] = int(years_missing_mask.sum())
        for lvl, median_yr in EXPERIENCE_LEVEL_MEDIANS.items():
            mask = df["experience_years"].isna() & (df["experience_level"] == lvl)
            df.loc[mask, "experience_years"] = median_yr

        # For remaining missing experience_years (where level was also missing), impute overall median
        overall_exp_median = df["experience_years"].median()
        df["experience_years"] = df["experience_years"].fillna(overall_exp_median)
        df["experience_level"] = df["experience_level"].fillna("Mid-level")

        # 4. Salary Validation & Target Variable Formulation (Strict Salary Rule)
        # Check integrity: both bounds positive, min <= max, not null
        valid_sal_mask = (
            df["salary_min_lpa"].notna()
            & df["salary_max_lpa"].notna()
            & (df["salary_min_lpa"] > 0)
            & (df["salary_max_lpa"] > 0)
            & (df["salary_min_lpa"] <= df["salary_max_lpa"])
        )
        
        df["is_salary_valid"] = valid_sal_mask
        self.cleaning_report["valid_salary_records_count"] = int(valid_sal_mask.sum())
        self.cleaning_report["invalid_or_missing_salary_count"] = int((~valid_sal_mask).sum())

        # Calculate salary mid-point (LPA) and annual INR only on valid records
        df["salary_mid_lpa"] = np.nan
        df["salary_annual_inr"] = np.nan
        df.loc[valid_sal_mask, "salary_mid_lpa"] = (
            (df.loc[valid_sal_mask, "salary_min_lpa"] + df.loc[valid_sal_mask, "salary_max_lpa"]) / 2.0
        ).round(2)
        df.loc[valid_sal_mask, "salary_annual_inr"] = (
            df.loc[valid_sal_mask, "salary_mid_lpa"] * 100000.0
        ).round(0)

        # 5. Skills Normalization
        cleaned_skills_tuples = df["skills_required"].apply(clean_skills)
        df["skills_required_clean"] = [t[0] for t in cleaned_skills_tuples]
        df["skill_count"] = [len(t[1]) for t in cleaned_skills_tuples]

        # 6. Date Parsing & Temporal Features
        df["posted_date_dt"] = pd.to_datetime(df["posted_date"], errors="coerce")
        df["posted_year"] = df["posted_date_dt"].dt.year
        df["posted_month"] = df["posted_date_dt"].dt.month
        df["posted_quarter"] = df["posted_date_dt"].dt.quarter

        # 7. Fill missing labels for categorical exploration (avoiding arbitrary data dropping)
        df["company_name"] = df["company_name"].fillna("Confidential")
        df["city"] = df["city"].fillna("Unknown")
        df["state"] = df["state"].fillna("Unknown")
        df["work_mode"] = df["work_mode"].fillna("Unknown")
        df["education"] = df["education"].fillna("Unknown")
        df["company_size"] = df["company_size"].fillna("Unknown")
        df["industry"] = df["industry"].fillna("Unknown")

        return df

    def extract_salary_model_data(self, df_cleaned: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only high-integrity records with verified salary for supervised regression.
        Guarantees zero fabricated salary data.
        """
        df_model = df_cleaned[df_cleaned["is_salary_valid"]].copy()
        # Drop synthetic identifiers and uninformative fields for ML modeling
        cols_to_drop = ["job_id", "job_url", "data_source", "salary_currency"]
        df_model = df_model.drop(columns=[c for c in cols_to_drop if c in df_model.columns])
        return df_model.reset_index(drop=True)

    def save_processed_datasets(
        self,
        df_cleaned_all: pd.DataFrame,
        df_model_salary: pd.DataFrame,
        output_dir: str = "data/processed",
    ) -> Tuple[str, str]:
        """Save cleaned datasets to disk."""
        os.makedirs(output_dir, exist_ok=True)
        path_all = os.path.join(output_dir, "cleaned_job_market_all.csv")
        path_salary = os.path.join(output_dir, "cleaned_salary_model_data.csv")

        df_cleaned_all.to_csv(path_all, index=False)
        df_model_salary.to_csv(path_salary, index=False)
        return path_all, path_salary


def run_preprocessing_pipeline(
    raw_path: str = "data/raw/india_job_market_messy_31150_records.csv",
    output_dir: str = "data/processed",
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, any]]:
    """Convenience function to run the complete preprocessing pipeline."""
    preprocessor = JobMarketPreprocessor(raw_filepath=raw_path)
    df_raw = preprocessor.load_data()
    df_cleaned = preprocessor.clean_dataset(df_raw)
    df_salary = preprocessor.extract_salary_model_data(df_cleaned)
    path_all, path_sal = preprocessor.save_processed_datasets(df_cleaned, df_salary, output_dir=output_dir)
    print(f"Cleaned dataset saved: {path_all} ({len(df_cleaned):,} rows)")
    print(f"Salary model dataset saved: {path_sal} ({len(df_salary):,} rows)")
    return df_cleaned, df_salary, preprocessor.cleaning_report


if __name__ == "__main__":
    run_preprocessing_pipeline()
