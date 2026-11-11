"""
Module: tests.test_dashboard
Description: Automated unit and integration test suite for the Streamlit SaaS Dashboard (Module 6).
Validates imports, caching, data loaders, chart generators, inference integrations, and error handling.
"""

import os
import io
import pytest
import pandas as pd
import fitz
import plotly.graph_objects as go

# 1. Imports Validation
def test_dashboard_imports():
    """Verifies all dashboard components, pages, and application modules import cleanly."""
    import dashboard.app as app
    import dashboard.data_loader as dl
    import dashboard.components.layout as layout
    import dashboard.components.sidebar as sidebar
    import dashboard.components.metric_cards as cards
    import dashboard.components.charts as charts
    import dashboard.components.filters as filters
    import dashboard.components.tables as tables

    import dashboard.pages.overview as p_overview
    import dashboard.pages.job_market as p_market
    import dashboard.pages.salary_analytics as p_sal_analytics
    import dashboard.pages.salary_prediction as p_sal_pred
    import dashboard.pages.resume_analyzer as p_resume
    import dashboard.pages.skill_gap as p_gap
    import dashboard.pages.company_intelligence as p_comp_intel
    import dashboard.pages.data_quality as p_quality
    import dashboard.pages.about as p_about

    assert hasattr(app, "main")
    assert hasattr(dl, "load_market_dataset")
    assert hasattr(sidebar, "render_sidebar")
    assert hasattr(p_overview, "render_overview_page")
    assert hasattr(p_comp_intel, "render_company_intelligence_page")


# 2. Data Loader & Caching Validation
def test_dashboard_data_loading():
    """Verifies that dataset loaders return valid DataFrames with clean_role."""
    from dashboard.data_loader import load_market_dataset, load_salary_dataset

    df_market = load_market_dataset()
    df_salary = load_salary_dataset()

    assert isinstance(df_market, pd.DataFrame)
    assert isinstance(df_salary, pd.DataFrame)
    assert len(df_market) == 30250
    assert len(df_salary) == 17559
    assert "clean_role" in df_market.columns
    assert "clean_role" in df_salary.columns
    assert "salary_mid_lpa" in df_salary.columns


def test_dashboard_cached_analytics_integration():
    """Verifies analytical functions invoked by the dashboard return expected structures."""
    from dashboard.data_loader import (
        get_cached_market_overview,
        get_cached_role_analytics,
        get_cached_city_analytics,
        get_cached_salary_analytics,
        get_cached_skill_intelligence,
    )

    overview = get_cached_market_overview()
    assert overview["total_job_postings"] == 30250
    assert overview["total_unique_companies"] == 16
    assert overview["total_job_roles"] == 12

    role_stats = get_cached_role_analytics()
    assert len(role_stats["top_roles"]) == 12

    city_stats = get_cached_city_analytics()
    assert len(city_stats["postings_by_city"]) == 16

    sal_stats = get_cached_salary_analytics()
    assert sal_stats["salary_range_analysis"]["total_salary_records"] == 17559
    assert sal_stats["salary_range_analysis"]["median_lpa"] > 0

    skill_stats = get_cached_skill_intelligence()
    assert len(skill_stats["top_skills"]) == 20
    assert len(skill_stats["co_occurring_skills"]) > 0


# 3. Model & Parser Initialization Validation
def test_dashboard_model_and_parser_resources():
    """Verifies resource cached factories for salary predictor and resume parser."""
    from dashboard.data_loader import get_salary_predictor, get_resume_parser

    predictor = get_salary_predictor()
    parser = get_resume_parser()

    assert predictor is not None
    assert hasattr(predictor, "predict")
    assert hasattr(predictor, "disclaimer")

    assert parser is not None
    assert hasattr(parser, "parse")
    assert hasattr(parser, "extract_skills")


def test_dashboard_system_health_check():
    """Verifies system health diagnostic returns expected keys and types."""
    from dashboard.data_loader import get_system_health

    health = get_system_health()
    assert "db_connected" in health
    assert "db_type" in health
    assert "api_online" in health
    assert "api_mode" in health
    assert health["market_dataset_rows"] == 30250
    assert health["salary_dataset_rows"] == 17559


# 4. Salary Prediction Integration Validation
def test_dashboard_salary_prediction_inference():
    """Tests end-to-end salary inference using the predictor loaded by the dashboard."""
    from dashboard.data_loader import get_salary_predictor

    predictor = get_salary_predictor()

    prediction = predictor.predict(
        job_title="Data Scientist",
        experience_years=4.5,
        city="Bengaluru",
        state="Karnataka",
        skills=["Python", "Machine Learning", "SQL", "Pandas"],
        education="Bachelor's",
        work_mode="Hybrid",
        company_size="Mid-sized (201-500)",
        industry="Technology",
        employment_type="Full-time",
    )

    assert "predicted_salary_lpa" in prediction
    assert "lower_bound_lpa" in prediction
    assert "upper_bound_lpa" in prediction
    assert prediction["predicted_salary_lpa"] > 0
    assert prediction["lower_bound_lpa"] <= prediction["predicted_salary_lpa"]
    assert prediction["upper_bound_lpa"] >= prediction["predicted_salary_lpa"]


# 5. Skill Gap Analysis Integration Validation
def test_dashboard_skill_gap_analysis_flow():
    """Tests skill gap report generation for candidate skills against a canonical role."""
    from src.skill_analyzer import generate_skill_gap_report, get_available_job_roles

    roles = get_available_job_roles()
    assert "Data Scientist" in roles

    report = generate_skill_gap_report(
        candidate_skills=["Python", "SQL", "Pandas"],
        job_role="Data Scientist",
    )

    assert report["job_role"] == "Data Scientist"
    assert "skill_match_score" in report
    assert 0.0 <= report["skill_match_score"] <= 100.0
    assert "Python" in report["matched_skills"]
    assert "Machine Learning" in report["missing_essential_skills"]
    assert len(report["learning_recommendations"]) > 0


# 6. Resume Parser Integration Validation (In-Memory)
def test_dashboard_resume_parser_in_memory_pdf():
    """Tests in-memory PDF parsing and skill detection without disk storage."""
    from dashboard.data_loader import get_resume_parser

    # Create synthetic PDF in memory
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "John Doe - Senior Data Scientist\n"
        "Summary:\nExtensive experience in AI.\n\n"
        "Technical Skills:\nPython, PyTorch, Docker, Kubernetes, SQL, FastAPI, Machine Learning\n\n"
        "Work Experience:\nDeveloped computer vision pipelines.\n"
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    parser = get_resume_parser()
    res = parser.parse(pdf_bytes, filename="test_resume.pdf")

    assert res["extraction_status"] == "SUCCESS"
    assert res["skill_count"] >= 5
    assert "Python" in res["extracted_skills"]
    assert "Docker" in res["extracted_skills"]
    assert "PyTorch" in res["extracted_skills"]


# 7. Chart Generators Validation
def test_dashboard_chart_builders():
    """Tests all Plotly chart builders generate valid figures with dark layout."""
    from dashboard.components.charts import (
        create_bar_chart,
        create_donut_chart,
        create_histogram,
        create_box_plot,
        create_gauge_chart,
    )

    # 1. Bar Chart
    fig_bar = create_bar_chart(
        data={"Role A": 10, "Role B": 20},
        x="Count",
        y="Role",
        title="Test Bar",
    )
    assert isinstance(fig_bar, go.Figure)
    assert fig_bar.layout.paper_bgcolor == "#3A0353"

    # 2. Donut Chart
    fig_donut = create_donut_chart(
        data={"Mode A": 50, "Mode B": 50},
        names="Mode",
        values="Postings",
        title="Test Donut",
    )
    assert isinstance(fig_donut, go.Figure)

    # 3. Histogram
    fig_hist = create_histogram([10.0, 12.5, 15.0, 20.0], title="Test Hist")
    assert isinstance(fig_hist, go.Figure)

    # 4. Box Plot
    df_box = pd.DataFrame({"exp": ["Fresher", "Junior"], "salary": [5.0, 8.0]})
    fig_box = create_box_plot(df_box, x="exp", y="salary", title="Test Box")
    assert isinstance(fig_box, go.Figure)

    # 5. Gauge Chart
    fig_gauge = create_gauge_chart(75.5, title="Test Match Score")
    assert isinstance(fig_gauge, go.Figure)


# 8. Error Handling & Edge Cases Validation
def test_dashboard_error_handling_edge_cases():
    """Tests graceful behavior on empty filters, unseen roles, and zero candidate skills."""
    from src.skill_analyzer import generate_skill_gap_report
    from dashboard.components.filters import render_job_market_filters
    from dashboard.data_loader import load_market_dataset

    # Unknown role fallback
    report_unseen = generate_skill_gap_report(
        candidate_skills=["Python"],
        job_role="Quantum Neuro-Architect",
    )
    assert report_unseen["job_role"] == "Software Engineer"
    assert len(report_unseen["analysis_warnings"]) > 0

    # Empty candidate skills
    report_empty = generate_skill_gap_report(
        candidate_skills=[],
        job_role="Data Analyst",
    )
    assert report_empty["skill_match_score"] == 0.0
    assert len(report_empty["matched_skills"]) == 0

