"""
Module: Job Market Intelligence Engine
Description: High-performance analytical engine computing job market overviews,
role-level intelligence, geographic distributions, salary analytics, skill co-occurrence,
and temporal trends from verified dataset splits.
"""

import os
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.skill_analyzer import (
    ROLE_NORMALIZATION_MAP,
    get_dataset,
    normalize_role_title,
)

DEFAULT_ALL_DATA_PATH = os.path.join("data", "processed", "cleaned_job_market_all.csv")
DEFAULT_SALARY_DATA_PATH = os.path.join("data", "processed", "cleaned_salary_model_data.csv")

_CACHED_ALL_DF: Optional[pd.DataFrame] = None
_CACHED_SALARY_DF: Optional[pd.DataFrame] = None


def get_market_dataset(data_path: Optional[str] = None) -> pd.DataFrame:
    """Loads and caches the full cleaned job market dataset (30,250 rows)."""
    global _CACHED_ALL_DF
    if _CACHED_ALL_DF is not None and data_path is None:
        return _CACHED_ALL_DF

    path = data_path or DEFAULT_ALL_DATA_PATH
    if not os.path.exists(path):
        candidate_paths = [
            path,
            os.path.join("..", path),
            os.path.join("data", "processed", "cleaned_job_market_all.csv"),
            os.path.join("..", "data", "processed", "cleaned_job_market_all.csv"),
        ]
        path = next((p for p in candidate_paths if os.path.exists(p)), None)

    if path is None or not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned job market dataset not found at: {path}")

    df = pd.read_csv(path)
    df["clean_role"] = (
        df["job_title"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(ROLE_NORMALIZATION_MAP)
        .fillna(df["job_title"].astype(str).str.strip().str.title())
    )

    if data_path is None:
        _CACHED_ALL_DF = df
    return df


def get_salary_dataset(data_path: Optional[str] = None) -> pd.DataFrame:
    """Loads and caches the verified salary modeling dataset (17,559 rows)."""
    global _CACHED_SALARY_DF
    if _CACHED_SALARY_DF is not None and data_path is None:
        return _CACHED_SALARY_DF

    path = data_path or DEFAULT_SALARY_DATA_PATH
    if not os.path.exists(path):
        candidate_paths = [
            path,
            os.path.join("..", path),
            os.path.join("data", "processed", "cleaned_salary_model_data.csv"),
            os.path.join("..", "data", "processed", "cleaned_salary_model_data.csv"),
        ]
        path = next((p for p in candidate_paths if os.path.exists(p)), None)

    if path is None or not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned salary modeling dataset not found at: {path}")

    df = pd.read_csv(path)
    df["clean_role"] = (
        df["job_title"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(ROLE_NORMALIZATION_MAP)
        .fillna(df["job_title"].astype(str).str.strip().str.title())
    )

    if data_path is None:
        _CACHED_SALARY_DF = df
    return df


# ---------------------------------------------------------
# A. MARKET OVERVIEW ANALYTICS
# ---------------------------------------------------------

def get_market_overview(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Computes high-level macro market KPIs and categorical distributions.
    """
    dataset = df if df is not None else get_market_dataset()
    total_postings = int(len(dataset))
    if total_postings == 0:
        return {
            "total_job_postings": 0,
            "total_unique_companies": 0,
            "total_job_roles": 0,
            "total_cities": 0,
            "employment_type_distribution": {},
            "work_mode_distribution": {},
            "experience_level_distribution": {},
        }

    unique_companies = int(dataset["company_name"].nunique()) if "company_name" in dataset.columns else 0
    unique_roles = int(dataset["clean_role"].nunique())
    unique_cities = int(dataset["city"].nunique()) if "city" in dataset.columns else 0

    emp_dist = dataset["employment_type"].value_counts().to_dict() if "employment_type" in dataset.columns else {}
    wm_dist = dataset["work_mode"].value_counts().to_dict() if "work_mode" in dataset.columns else {}
    exp_dist = dataset["experience_level"].value_counts().to_dict() if "experience_level" in dataset.columns else {}

    return {
        "total_job_postings": total_postings,
        "total_unique_companies": unique_companies,
        "total_job_roles": unique_roles,
        "total_cities": unique_cities,
        "employment_type_distribution": {str(k): int(v) for k, v in emp_dist.items()},
        "work_mode_distribution": {str(k): int(v) for k, v in wm_dist.items()},
        "experience_level_distribution": {str(k): int(v) for k, v in exp_dist.items()},
    }


# ---------------------------------------------------------
# B. JOB ROLE ANALYTICS
# ---------------------------------------------------------

def get_job_role_analytics(df: Optional[pd.DataFrame] = None, top_n: int = 10) -> Dict[str, Any]:
    """
    Computes job role demand rankings and multi-dimensional cross-tabulations.
    """
    dataset = df if df is not None else get_market_dataset()
    total_postings = len(dataset)
    if total_postings == 0:
        return {
            "postings_by_role": {},
            "top_roles": [],
            "role_by_experience": {},
            "role_by_city": {},
            "employment_type_by_role": {},
        }

    role_counts = dataset["clean_role"].value_counts()
    postings_by_role = {str(k): int(v) for k, v in role_counts.items()}

    top_roles = []
    for rank, (role, count) in enumerate(role_counts.head(top_n).items(), 1):
        share_pct = round((count / total_postings) * 100, 2)
        top_roles.append({
            "rank": rank,
            "role": str(role),
            "job_count": int(count),
            "share_percentage": share_pct,
        })

    # Cross tabulations
    role_exp_ct = pd.crosstab(dataset["clean_role"], dataset["experience_level"]).to_dict(orient="index")
    role_exp_dict = {str(r): {str(e): int(cnt) for e, cnt in vals.items()} for r, vals in role_exp_ct.items()}

    role_city_ct = pd.crosstab(dataset["clean_role"], dataset["city"]).to_dict(orient="index")
    role_city_dict = {str(r): {str(c): int(cnt) for c, cnt in vals.items()} for r, vals in role_city_ct.items()}

    role_emp_ct = pd.crosstab(dataset["clean_role"], dataset["employment_type"]).to_dict(orient="index")
    role_emp_dict = {str(r): {str(emp): int(cnt) for emp, cnt in vals.items()} for r, vals in role_emp_ct.items()}

    return {
        "postings_by_role": postings_by_role,
        "top_roles": top_roles,
        "role_by_experience": role_exp_dict,
        "role_by_city": role_city_dict,
        "employment_type_by_role": role_emp_dict,
    }


# ---------------------------------------------------------
# C. CITY-WISE & GEOGRAPHIC ANALYTICS
# ---------------------------------------------------------

def get_city_analytics(df: Optional[pd.DataFrame] = None, top_n: int = 10) -> Dict[str, Any]:
    """
    Computes hiring concentration across tech hubs, work mode allocations, and state shares.
    """
    dataset = df if df is not None else get_market_dataset()
    total_postings = len(dataset)
    if total_postings == 0 or "city" not in dataset.columns:
        return {
            "postings_by_city": {},
            "top_cities": [],
            "role_demand_by_city": {},
            "work_mode_by_city": {},
            "state_distribution": {},
        }

    city_counts = dataset["city"].value_counts()
    postings_by_city = {str(k): int(v) for k, v in city_counts.items()}

    top_cities = []
    for rank, (city, count) in enumerate(city_counts.head(top_n).items(), 1):
        share_pct = round((count / total_postings) * 100, 2)
        top_cities.append({
            "rank": rank,
            "city": str(city),
            "job_count": int(count),
            "share_percentage": share_pct,
        })

    # Work mode by city
    wm_city_ct = pd.crosstab(dataset["city"], dataset["work_mode"]).to_dict(orient="index")
    wm_city_dict = {str(c): {str(wm): int(cnt) for wm, cnt in vals.items()} for c, vals in wm_city_ct.items()}

    # Role demand by city
    role_city_ct = pd.crosstab(dataset["city"], dataset["clean_role"]).to_dict(orient="index")
    role_city_dict = {str(c): {str(r): int(cnt) for r, cnt in vals.items()} for c, vals in role_city_ct.items()}

    # State distribution
    state_dist = dataset["state"].value_counts().to_dict() if "state" in dataset.columns else {}
    state_dict = {str(k): int(v) for k, v in state_dist.items()}

    return {
        "postings_by_city": postings_by_city,
        "top_cities": top_cities,
        "role_demand_by_city": role_city_dict,
        "work_mode_by_city": wm_city_dict,
        "state_distribution": state_dict,
    }


# ---------------------------------------------------------
# D. SALARY ANALYTICS (EXCLUSIVELY ON VERIFIED SALARY SET)
# ---------------------------------------------------------

def get_salary_analytics(salary_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Analyzes compensation benchmarks using exclusively the verified salary modeling dataset
    (`cleaned_salary_model_data.csv`).
    Target variable: salary_mid_lpa (INR Lakhs Per Annum).
    """
    df_sal = salary_df if salary_df is not None else get_salary_dataset()
    if len(df_sal) == 0:
        return {}

    # 1. Salary by Job Role
    role_group = df_sal.groupby("clean_role")["salary_mid_lpa"]
    mean_by_role = {str(k): round(float(v), 2) for k, v in role_group.mean().items()}
    median_by_role = {str(k): round(float(v), 2) for k, v in role_group.median().items()}

    # Top paying roles sorted by median
    top_paying_roles = []
    ranked_roles = (
        role_group.agg(["count", "mean", "median", "min", "max", "std"])
        .sort_values(by="median", ascending=False)
        .reset_index()
    )
    for rank, row in ranked_roles.iterrows():
        top_paying_roles.append({
            "rank": rank + 1,
            "role": str(row["clean_role"]),
            "job_count": int(row["count"]),
            "median_lpa": round(float(row["median"]), 2),
            "mean_lpa": round(float(row["mean"]), 2),
            "min_lpa": round(float(row["min"]), 2),
            "max_lpa": round(float(row["max"]), 2),
        })

    # 2. Salary by Experience Level
    exp_order = ["Fresher", "Junior", "Mid-level", "Senior", "Lead"]
    exp_group = df_sal.groupby("experience_level")["salary_mid_lpa"]
    salary_by_experience = {}
    for exp_lvl in exp_order:
        sub_exp = df_sal[df_sal["experience_level"] == exp_lvl]["salary_mid_lpa"]
        if len(sub_exp) > 0:
            salary_by_experience[exp_lvl] = {
                "count": int(len(sub_exp)),
                "mean_lpa": round(float(sub_exp.mean()), 2),
                "median_lpa": round(float(sub_exp.median()), 2),
                "p25_lpa": round(float(sub_exp.quantile(0.25)), 2),
                "p75_lpa": round(float(sub_exp.quantile(0.75)), 2),
                "min_lpa": round(float(sub_exp.min()), 2),
                "max_lpa": round(float(sub_exp.max()), 2),
            }

    # 3. Salary by City
    city_group = df_sal.groupby("city")["salary_mid_lpa"].agg(["count", "mean", "median"]).reset_index()
    salary_by_city = {}
    for _, row in city_group.iterrows():
        salary_by_city[str(row["city"])] = {
            "count": int(row["count"]),
            "mean_lpa": round(float(row["mean"]), 2),
            "median_lpa": round(float(row["median"]), 2),
        }

    # 4. Salary by Work Mode
    wm_group = df_sal.groupby("work_mode")["salary_mid_lpa"].agg(["count", "mean", "median"]).reset_index()
    salary_by_work_mode = {}
    for _, row in wm_group.iterrows():
        salary_by_work_mode[str(row["work_mode"])] = {
            "count": int(row["count"]),
            "mean_lpa": round(float(row["mean"]), 2),
            "median_lpa": round(float(row["median"]), 2),
        }

    # 5. Overall Salary Range Analysis
    all_sal = df_sal["salary_mid_lpa"]
    salary_range_analysis = {
        "total_salary_records": int(len(all_sal)),
        "mean_lpa": round(float(all_sal.mean()), 2),
        "median_lpa": round(float(all_sal.median()), 2),
        "std_lpa": round(float(all_sal.std()), 2),
        "p25_lpa": round(float(all_sal.quantile(0.25)), 2),
        "p75_lpa": round(float(all_sal.quantile(0.75)), 2),
        "min_lpa": round(float(all_sal.min()), 2),
        "max_lpa": round(float(all_sal.max()), 2),
    }

    return {
        "average_salary_by_role": mean_by_role,
        "median_salary_by_role": median_by_role,
        "salary_by_experience": salary_by_experience,
        "salary_by_city": salary_by_city,
        "salary_by_work_mode": salary_by_work_mode,
        "salary_range_analysis": salary_range_analysis,
        "top_paying_roles": top_paying_roles,
    }


# ---------------------------------------------------------
# E. TECHNICAL SKILL INTELLIGENCE & CO-OCCURRENCE
# ---------------------------------------------------------

def get_skill_intelligence(df: Optional[pd.DataFrame] = None, top_n: int = 20) -> Dict[str, Any]:
    """
    Computes overall top skills, multi-dimensional demand slices, and pairwise
    skill co-occurrence matrices without duplicate counting per job posting.
    """
    dataset = df if df is not None else get_market_dataset()
    total_postings = len(dataset)
    if total_postings == 0:
        return {"top_skills": [], "co_occurring_skills": []}

    # 1. Overall Top Skills
    skill_counts = Counter()
    posting_skill_sets: List[Set[str]] = []

    for s_str in dataset["skills_required_clean"].dropna():
        unique_skills = set(s.strip() for s in str(s_str).split(",") if s.strip())
        posting_skill_sets.append(unique_skills)
        for s in unique_skills:
            skill_counts[s] += 1

    top_skills = []
    for rank, (skill, count) in enumerate(skill_counts.most_common(top_n), 1):
        top_skills.append({
            "rank": rank,
            "skill": skill,
            "job_count": int(count),
            "demand_percentage": round((count / total_postings) * 100, 2),
        })

    # 2. Pairwise Skill Co-occurrence
    pair_counts = Counter()
    for skill_set in posting_skill_sets:
        sorted_skills = sorted(list(skill_set))
        num_skills = len(sorted_skills)
        for i in range(num_skills):
            for j in range(i + 1, num_skills):
                pair = (sorted_skills[i], sorted_skills[j])
                pair_counts[pair] += 1

    co_occurring_skills = []
    for (s1, s2), count in pair_counts.most_common(15):
        co_occurring_skills.append({
            "skill_pair": f"{s1} + {s2}",
            "skill_1": s1,
            "skill_2": s2,
            "co_occurrence_count": int(count),
            "co_occurrence_percentage": round((count / total_postings) * 100, 2),
        })

    return {
        "top_skills": top_skills,
        "co_occurring_skills": co_occurring_skills,
    }


# ---------------------------------------------------------
# F. TEMPORAL TRENDS & DATA LIMITATIONS
# ---------------------------------------------------------

def get_temporal_trends(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Analyzes monthly and quarterly posting counts from available date columns.
    Clearly documents the simulated nature of the underlying posting timestamps.
    """
    dataset = df if df is not None else get_market_dataset()

    monthly_postings: List[Dict[str, Any]] = []
    quarterly_postings: List[Dict[str, Any]] = []

    if "posted_date_dt" in dataset.columns and dataset["posted_date_dt"].notna().any():
        valid_dates = dataset[dataset["posted_date_dt"].notna()].copy()
        # Parse year-month string
        valid_dates["year_month"] = valid_dates["posted_date_dt"].str.slice(0, 7)
        ym_counts = valid_dates["year_month"].value_counts().sort_index()
        for ym, cnt in ym_counts.items():
            monthly_postings.append({
                "period": str(ym),
                "posting_count": int(cnt),
            })

    if "posted_year" in dataset.columns and "posted_quarter" in dataset.columns:
        valid_q = dataset[dataset["posted_year"].notna() & dataset["posted_quarter"].notna()].copy()
        valid_q["year_quarter"] = (
            valid_q["posted_year"].astype(int).astype(str) + "-Q" + valid_q["posted_quarter"].astype(int).astype(str)
        )
        yq_counts = valid_q["year_quarter"].value_counts().sort_index()
        for yq, cnt in yq_counts.items():
            quarterly_postings.append({
                "quarter": str(yq),
                "posting_count": int(cnt),
            })

    return {
        "monthly_postings": monthly_postings,
        "quarterly_postings": quarterly_postings,
        "data_limitation_note": (
            "Temporal distributions reflect the synthetic generation timestamps present in the dataset (2024 - 2026). "
            "They illustrate relative monthly cadence and development stability, but do not represent macroeconomic or real-time Indian labor trends."
        ),
    }


# ---------------------------------------------------------
# G. ROLE & CITY SPECIFIC DEEP DOSSIERS
# ---------------------------------------------------------

def get_role_dossier(job_role: str, df: Optional[pd.DataFrame] = None, salary_df: Optional[pd.DataFrame] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a comprehensive 360-degree dossier for a specific job role.
    """
    market_df = df if df is not None else get_market_dataset()
    sal_df = salary_df if salary_df is not None else get_salary_dataset()

    canonical_role = normalize_role_title(job_role)
    sub_market = market_df[market_df["clean_role"] == canonical_role]
    if len(sub_market) == 0:
        return None

    sub_sal = sal_df[sal_df["clean_role"] == canonical_role]["salary_mid_lpa"]

    # Skill demand for this role
    skill_counts = Counter()
    for s_str in sub_market["skills_required_clean"].dropna():
        for s in set(s.strip() for s in str(s_str).split(",") if s.strip()):
            skill_counts[s] += 1

    role_skills = [
        {"skill": s, "count": int(cnt), "demand_percentage": round((cnt / len(sub_market)) * 100, 2)}
        for s, cnt in skill_counts.most_common(10)
    ]

    city_hiring = sub_market["city"].value_counts().head(5).to_dict()
    wm_dist = sub_market["work_mode"].value_counts().to_dict()

    return {
        "job_role": canonical_role,
        "total_postings": int(len(sub_market)),
        "share_of_market_pct": round((len(sub_market) / len(market_df)) * 100, 2),
        "salary_stats": {
            "sample_count": int(len(sub_sal)),
            "median_lpa": round(float(sub_sal.median()), 2) if len(sub_sal) > 0 else None,
            "mean_lpa": round(float(sub_sal.mean()), 2) if len(sub_sal) > 0 else None,
            "min_lpa": round(float(sub_sal.min()), 2) if len(sub_sal) > 0 else None,
            "max_lpa": round(float(sub_sal.max()), 2) if len(sub_sal) > 0 else None,
        },
        "top_skills": role_skills,
        "top_cities": {str(k): int(v) for k, v in city_hiring.items()},
        "work_mode_distribution": {str(k): int(v) for k, v in wm_dist.items()},
    }


def get_city_dossier(city_name: str, df: Optional[pd.DataFrame] = None, salary_df: Optional[pd.DataFrame] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a comprehensive 360-degree dossier for a specific hiring city.
    """
    market_df = df if df is not None else get_market_dataset()
    sal_df = salary_df if salary_df is not None else get_salary_dataset()

    city_clean = str(city_name).strip().title()
    sub_market = market_df[market_df["city"].str.strip().str.title() == city_clean]
    if len(sub_market) == 0:
        return None

    sub_sal = sal_df[sal_df["city"].str.strip().str.title() == city_clean]["salary_mid_lpa"]

    top_roles = sub_market["clean_role"].value_counts().head(5).to_dict()
    wm_dist = sub_market["work_mode"].value_counts().to_dict()

    # Skills demanded in this city
    skill_counts = Counter()
    for s_str in sub_market["skills_required_clean"].dropna():
        for s in set(s.strip() for s in str(s_str).split(",") if s.strip()):
            skill_counts[s] += 1

    top_skills = [
        {"skill": s, "count": int(cnt), "demand_percentage": round((cnt / len(sub_market)) * 100, 2)}
        for s, cnt in skill_counts.most_common(10)
    ]

    return {
        "city": city_clean,
        "state": str(sub_market["state"].iloc[0]) if "state" in sub_market.columns and not sub_market["state"].empty else "Unknown",
        "total_postings": int(len(sub_market)),
        "share_of_market_pct": round((len(sub_market) / len(market_df)) * 100, 2),
        "salary_stats": {
            "sample_count": int(len(sub_sal)),
            "median_lpa": round(float(sub_sal.median()), 2) if len(sub_sal) > 0 else None,
            "mean_lpa": round(float(sub_sal.mean()), 2) if len(sub_sal) > 0 else None,
        },
        "top_roles": {str(k): int(v) for k, v in top_roles.items()},
        "top_skills": top_skills,
        "work_mode_distribution": {str(k): int(v) for k, v in wm_dist.items()},
    }

