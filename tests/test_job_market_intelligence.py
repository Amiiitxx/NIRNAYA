"""
Unit tests for Module 5: Job Market Intelligence Engine (src/job_market_intelligence.py)
Tests cover macro market KPIs, role distributions, geographic concentrations,
verified salary analytics, skill co-occurrence, and temporal trends.
"""

import pytest
import pandas as pd

from src.job_market_intelligence import (
    get_market_overview,
    get_job_role_analytics,
    get_city_analytics,
    get_salary_analytics,
    get_skill_intelligence,
    get_temporal_trends,
    get_role_dossier,
    get_city_dossier,
)


def test_market_overview_metrics():
    """Verify macro market overview metrics against 30,250 cleaned postings."""
    overview = get_market_overview()

    assert overview["total_job_postings"] == 30250
    assert overview["total_unique_companies"] == 16
    assert overview["total_job_roles"] == 12
    assert overview["total_cities"] == 16

    # Verify distribution sums
    emp_total = sum(overview["employment_type_distribution"].values())
    assert emp_total == 30250

    wm_total = sum(overview["work_mode_distribution"].values())
    assert wm_total == 30250

    exp_total = sum(overview["experience_level_distribution"].values())
    assert exp_total == 30250


def test_job_role_analytics():
    """Verify job role rankings and cross tabulations."""
    data = get_job_role_analytics(top_n=10)

    assert len(data["top_roles"]) == 10
    assert len(data["postings_by_role"]) == 12
    assert data["top_roles"][0]["rank"] == 1
    assert data["top_roles"][0]["job_count"] > 0
    assert data["top_roles"][0]["share_percentage"] > 0

    # Cross tabulations exist
    assert "Data Scientist" in data["role_by_experience"]
    assert "Fresher" in data["role_by_experience"]["Data Scientist"]
    assert "Bengaluru" in data["role_by_city"]["Data Scientist"]


def test_city_analytics():
    """Verify geographic tech hub concentration."""
    data = get_city_analytics(top_n=10)

    assert len(data["top_cities"]) == 10
    assert len(data["postings_by_city"]) == 16
    assert data["top_cities"][0]["rank"] == 1

    # Check top city is Bengaluru
    top_city_names = [c["city"] for c in data["top_cities"]]
    assert "Bengaluru" in top_city_names

    # State distribution
    assert len(data["state_distribution"]) > 0


def test_salary_analytics_verified_dataset():
    """Verify compensation metrics computed exclusively on cleaned_salary_model_data.csv."""
    sal_data = get_salary_analytics()

    assert sal_data["salary_range_analysis"]["total_salary_records"] == 17559
    assert sal_data["salary_range_analysis"]["mean_lpa"] > 0
    assert sal_data["salary_range_analysis"]["median_lpa"] > 0
    assert sal_data["salary_range_analysis"]["min_lpa"] > 0

    # Role salaries
    assert len(sal_data["median_salary_by_role"]) == 12
    assert len(sal_data["top_paying_roles"]) == 12

    # Senior roles should have higher median than Fresher
    exp_sal = sal_data["salary_by_experience"]
    assert exp_sal["Senior"]["median_lpa"] > exp_sal["Fresher"]["median_lpa"]
    assert exp_sal["Lead"]["median_lpa"] > exp_sal["Junior"]["median_lpa"]


def test_skill_intelligence_and_co_occurrence():
    """Verify top skills and pairwise skill co-occurrence."""
    skill_data = get_skill_intelligence(top_n=20)

    assert len(skill_data["top_skills"]) == 20
    assert skill_data["top_skills"][0]["rank"] == 1
    assert skill_data["top_skills"][0]["demand_percentage"] > 0

    # Co-occurrence
    assert len(skill_data["co_occurring_skills"]) > 0
    first_pair = skill_data["co_occurring_skills"][0]
    assert "skill_pair" in first_pair
    assert first_pair["co_occurrence_count"] > 0


def test_temporal_trends_data():
    """Verify monthly and quarterly posting aggregation."""
    trends = get_temporal_trends()

    assert len(trends["monthly_postings"]) > 0
    assert len(trends["quarterly_postings"]) > 0
    assert "data_limitation_note" in trends


def test_role_dossier():
    """Verify detailed role dossier for Data Scientist and invalid role handling."""
    dossier = get_role_dossier("Data Scientist")
    assert dossier is not None
    assert dossier["job_role"] == "Data Scientist"
    assert dossier["total_postings"] > 0
    assert dossier["salary_stats"]["median_lpa"] > 0
    assert len(dossier["top_skills"]) > 0

    # Invalid role
    assert get_role_dossier("NonExistentRoleXYZ123") is None


def test_city_dossier():
    """Verify detailed city dossier for Bengaluru and invalid city handling."""
    dossier = get_city_dossier("Bengaluru")
    assert dossier is not None
    assert dossier["city"] == "Bengaluru"
    assert dossier["total_postings"] > 0
    assert len(dossier["top_roles"]) > 0

    # Invalid city
    assert get_city_dossier("NonExistentCityXYZ123") is None

