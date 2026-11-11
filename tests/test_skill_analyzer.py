"""
Unit tests for Module 4: Skill Gap Analysis Engine (src/skill_analyzer.py)
Tests verify role retrieval, market demand aggregations, duplicate handling,
demand-weighted match scoring, priority classification, learning recommendations,
edge cases (empty skills, invalid roles), and integration with resume extraction.
"""

import pytest
import pandas as pd
import numpy as np

from src.skill_analyzer import (
    SkillGapAnalyzer,
    get_available_job_roles,
    analyze_market_skill_demand,
    get_role_required_skills,
    compare_candidate_skills,
    calculate_skill_match_score,
    generate_learning_recommendations,
    generate_skill_gap_report,
    normalize_role_title,
    normalize_candidate_skills,
)
from src.resume_parser import extract_skills_from_text


# ---------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------

@pytest.fixture
def synthetic_micro_dataset() -> pd.DataFrame:
    """
    Creates a controlled small synthetic dataset to verify mathematical accuracy.
    4 postings for 'Data Scientist', 2 postings for 'Software Engineer'.
    Data Scientist skills:
      Job 1: Python, Machine Learning, SQL, Python (duplicate in row)
      Job 2: Python, Machine Learning, Docker
      Job 3: Python, Machine Learning, Pandas
      Job 4: Machine Learning, AWS
    """
    data = [
        {"job_id": 1, "job_title": "Data Scientist", "skills_required_clean": "Python, Machine Learning, SQL, Python"},
        {"job_id": 2, "job_title": "Data Scientist", "skills_required_clean": "Python, Machine Learning, Docker"},
        {"job_id": 3, "job_title": "Data Scientist", "skills_required_clean": "Python, Machine Learning, Pandas"},
        {"job_id": 4, "job_title": "Data Scientist", "skills_required_clean": "Machine Learning, AWS"},
        {"job_id": 5, "job_title": "Software Engineer", "skills_required_clean": "Java, Spring, Docker"},
        {"job_id": 6, "job_title": "Software Engineer", "skills_required_clean": "Java, AWS, Kubernetes"},
    ]
    df = pd.DataFrame(data)
    df["clean_role"] = df["job_title"]
    return df


# ---------------------------------------------------------
# JOB ROLES & DATASET LOADING TESTS
# ---------------------------------------------------------

def test_get_available_job_roles():
    """Verify dynamic retrieval of canonical job roles from the dataset."""
    roles = get_available_job_roles()
    assert len(roles) >= 12
    assert "Data Scientist" in roles
    assert "Machine Learning Engineer" in roles
    assert "Software Engineer" in roles
    assert "Cloud Engineer" in roles


def test_normalize_role_title():
    """Verify case normalization and title mappings."""
    assert normalize_role_title("data scientist") == "Data Scientist"
    assert normalize_role_title("nlp engineer") == "NLP Engineer"
    assert normalize_role_title("ai engineer") == "AI Engineer"
    assert normalize_role_title("BI DEVELOPER") == "BI Developer"
    assert normalize_role_title("Software Engineer") == "Software Engineer"
    assert normalize_role_title(None) == "Software Engineer"


# ---------------------------------------------------------
# MARKET SKILL DEMAND ANALYSIS TESTS
# ---------------------------------------------------------

def test_overall_market_skill_demand():
    """Verify overall market skill demand metrics on actual dataset."""
    demand_df = analyze_market_skill_demand(top_n=10)
    assert len(demand_df) == 10
    assert "skill" in demand_df.columns
    assert "job_count" in demand_df.columns
    assert "demand_percentage" in demand_df.columns

    # Verify descending sort
    counts = demand_df["job_count"].tolist()
    assert counts == sorted(counts, reverse=True)
    # Python and ML should be top skills
    top_skills = demand_df["skill"].head(3).tolist()
    assert "Python" in top_skills or "Machine Learning" in top_skills


def test_grouped_market_skill_demand_by_role():
    """Verify grouped skill demand by job role."""
    df_role = analyze_market_skill_demand(by="clean_role", top_n=5)
    assert "clean_role" in df_role.columns
    assert "skill" in df_role.columns
    assert "demand_percentage" in df_role.columns
    assert df_role["clean_role"].nunique() >= 12


def test_grouped_market_skill_demand_by_experience():
    """Verify grouped skill demand by seniority level."""
    df_exp = analyze_market_skill_demand(by="experience_level", top_n=5)
    assert "experience_level" in df_exp.columns
    assert "demand_percentage" in df_exp.columns


# ---------------------------------------------------------
# MATHEMATICAL DEMAND & DUPLICATE HANDLING TESTS
# ---------------------------------------------------------

def test_duplicate_skill_in_same_posting_handled(synthetic_micro_dataset):
    """
    Verify that duplicate skills in the same job posting are counted only once.
    Job 1 has 'Python' twice, but Python should have count 3 across 4 jobs (75%).
    Machine Learning appears in all 4 jobs -> 100%.
    """
    skills = get_role_required_skills("Data Scientist", df=synthetic_micro_dataset)
    skill_dict = {s["skill"]: s for s in skills}

    assert skill_dict["Machine Learning"]["job_count"] == 4
    assert skill_dict["Machine Learning"]["demand_percentage"] == 100.0
    assert skill_dict["Python"]["job_count"] == 3
    assert skill_dict["Python"]["demand_percentage"] == 75.0
    assert skill_dict["SQL"]["job_count"] == 1
    assert skill_dict["SQL"]["demand_percentage"] == 25.0


def test_role_skill_priority_classification(synthetic_micro_dataset):
    """
    Verify classification:
    - Essential: demand >= 50% (ML 100%, Python 75%)
    - Important: demand >= 25% and < 50% (SQL 25%, Docker 25%, Pandas 25%, AWS 25%)
    - Additional: demand < 25% (0% here)
    """
    skills = get_role_required_skills(
        "Data Scientist",
        df=synthetic_micro_dataset,
        essential_threshold=50.0,
        important_threshold=25.0,
    )
    categories = {s["skill"]: s["category"] for s in skills}

    assert categories["Machine Learning"] == "Essential"
    assert categories["Python"] == "Essential"
    assert categories["SQL"] == "Important"
    assert categories["Docker"] == "Important"


# ---------------------------------------------------------
# CANDIDATE MATCHING & SCORE FORMULA TESTS
# ---------------------------------------------------------

def test_demand_weighted_skill_match_score_formula(synthetic_micro_dataset):
    """
    Manual Mathematical Verification:
    Data Scientist required skills:
      Machine Learning: 100.0% weight
      Python: 75.0% weight
      SQL: 25.0% weight
      Docker: 25.0% weight
      Pandas: 25.0% weight
      AWS: 25.0% weight
    Total weight = 100 + 75 + 25 + 25 + 25 + 25 = 275.0

    Candidate has: ['Python', 'SQL']
    Matched weight = 75.0 + 25.0 = 100.0
    Expected Score = (100.0 / 275.0) * 100 = 36.36%
    """
    score = calculate_skill_match_score(
        candidate_skills=["Python", "SQL"],
        job_role="Data Scientist",
        df=synthetic_micro_dataset,
    )
    assert score == pytest.approx(36.36, rel=1e-2)


def test_match_score_boundary_conditions(synthetic_micro_dataset):
    """Verify boundary conditions: 0% for no match, 100% for full match."""
    # Zero match
    zero_score = calculate_skill_match_score(
        candidate_skills=["Rust", "Solidity"],
        job_role="Data Scientist",
        df=synthetic_micro_dataset,
    )
    assert zero_score == 0.0

    # Empty candidate skills
    empty_score = calculate_skill_match_score(
        candidate_skills=[],
        job_role="Data Scientist",
        df=synthetic_micro_dataset,
    )
    assert empty_score == 0.0

    # Full match (all 6 required skills)
    full_skills = ["Python", "Machine Learning", "SQL", "Docker", "Pandas", "AWS"]
    full_score = calculate_skill_match_score(
        candidate_skills=full_skills,
        job_role="Data Scientist",
        df=synthetic_micro_dataset,
    )
    assert full_score == 100.0


def test_compare_candidate_skills(synthetic_micro_dataset):
    """Verify accurate partitioning of matched and missing skill categories."""
    comp = compare_candidate_skills(
        candidate_skills=["Python", "SQL"],
        job_role="Data Scientist",
        df=synthetic_micro_dataset,
        essential_threshold=50.0,
        important_threshold=25.0,
    )
    assert comp["total_required_skills"] == 6
    assert set(comp["matched_skills"]) == {"Python", "SQL"}
    assert "Machine Learning" in comp["missing_essential_skills"]
    assert "Docker" in comp["missing_important_skills"]
    assert comp["essential_match_count"] == 1  # Python matched
    assert comp["essential_missing_count"] == 1  # ML missing


# ---------------------------------------------------------
# LEARNING RECOMMENDATIONS TESTS
# ---------------------------------------------------------

def test_generate_learning_recommendations(synthetic_micro_dataset):
    """Verify learning recommendations prioritize missing Essential skills first."""
    recs = generate_learning_recommendations(
        candidate_skills=["Python", "SQL"],
        job_role="Data Scientist",
        df=synthetic_micro_dataset,
    )
    assert len(recs) == 4  # Missing: Machine Learning, Docker, Pandas, AWS

    # First recommendation MUST be Essential
    assert recs[0]["skill"] == "Machine Learning"
    assert recs[0]["priority"] == "Essential"
    assert "action" in recs[0]["suggested_learning_action"].lower() or "study" in recs[0]["suggested_learning_action"].lower()
    assert "project" in recs[0]["suggested_project_practice"].lower() or "build" in recs[0]["suggested_project_practice"].lower()


# ---------------------------------------------------------
# STRUCTURED SKILL GAP REPORT TESTS
# ---------------------------------------------------------

def test_generate_skill_gap_report_schema():
    """Verify complete dictionary schema returned by generate_skill_gap_report."""
    report = generate_skill_gap_report(
        candidate_skills=["Python", "SQL", "Scikit-learn"],
        job_role="Data Scientist",
    )
    required_keys = [
        "job_role",
        "total_required_skills",
        "matched_skills",
        "missing_skills",
        "missing_essential_skills",
        "missing_important_skills",
        "missing_additional_skills",
        "skill_match_score",
        "essential_match_count",
        "essential_missing_count",
        "learning_recommendations",
        "analysis_warnings",
    ]
    for key in required_keys:
        assert key in report, f"Report missing key: {key}"

    assert report["job_role"] == "Data Scientist"
    assert report["skill_match_score"] > 0.0
    assert isinstance(report["matched_skills"], list)
    assert isinstance(report["learning_recommendations"], list)


def test_invalid_job_role_fallback():
    """Verify graceful fallback and warning when an unrecognized role is provided."""
    report = generate_skill_gap_report(
        candidate_skills=["Python"],
        job_role="Quantum Cyber Ninja",
    )
    assert report["job_role"] == "Software Engineer"
    assert len(report["analysis_warnings"]) > 0
    assert "Quantum Cyber Ninja" in report["analysis_warnings"][0]


def test_empty_candidate_skills_warning():
    """Verify warning generated when candidate skills are empty."""
    report = generate_skill_gap_report(
        candidate_skills=[],
        job_role="Data Scientist",
    )
    assert report["skill_match_score"] == 0.0
    assert len(report["analysis_warnings"]) > 0
    assert "No candidate skills" in report["analysis_warnings"][0]


# ---------------------------------------------------------
# INTEGRATION WITH RESUME EXTRACTION TESTS
# ---------------------------------------------------------

def test_integration_with_resume_extraction():
    """Verify passing raw resume text directly into the skill gap analyzer."""
    resume_text = (
        "Experienced Engineer with strong background in Python, Docker, and PostgreSQL. "
        "Built microservices and scalable cloud endpoints on AWS."
    )
    # 1. Resume parser extracts skills
    extracted = extract_skills_from_text(resume_text)
    assert "Python" in extracted
    assert "Docker" in extracted
    assert "AWS" in extracted

    # 2. Skill gap analyzer accepts extracted skills
    report = generate_skill_gap_report(
        candidate_skills=extracted,
        job_role="Cloud Engineer",
    )
    assert "Docker" in report["matched_skills"]
    assert "AWS" in report["matched_skills"]
    assert report["skill_match_score"] > 0.0


def test_skill_gap_analyzer_class():
    """Verify SkillGapAnalyzer OOP wrapper methods."""
    analyzer = SkillGapAnalyzer()
    roles = analyzer.get_available_roles()
    assert "Data Scientist" in roles

    report = analyzer.generate_report(["Python", "SQL"], "Data Scientist")
    assert report["skill_match_score"] > 0.0

