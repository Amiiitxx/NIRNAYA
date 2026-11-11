"""
Module: dashboard.app
Description: Primary Streamlit application entrypoint for NIRNAYA — AI-Powered Career
& Job Market Intelligence Platform.
"""

import sys
import os

# Ensure project root is available on sys.path for local and deployed runs
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

# Configure page settings - MUST be first Streamlit command
st.set_page_config(
    page_title="NIRNAYA | AI-Powered Career & Market Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.components.layout import apply_custom_css, render_disclaimer
from dashboard.components.sidebar import render_sidebar
from dashboard.data_loader import get_system_health
from dashboard.pages.overview import render_overview_page
from dashboard.pages.job_market import render_job_market_page
from dashboard.pages.salary_analytics import render_salary_analytics_page
from dashboard.pages.salary_prediction import render_salary_prediction_page
from dashboard.pages.resume_analyzer import render_resume_analyzer_page
from dashboard.pages.skill_gap import render_skill_gap_page
from dashboard.pages.company_intelligence import render_company_intelligence_page
from dashboard.pages.data_quality import render_data_quality_page
from dashboard.pages.about import render_about_page


def main() -> None:
    """Main application orchestrator and router for NIRNAYA."""
    # 1. Apply NIRNAYA purple and orange custom styling
    apply_custom_css()

    # 2. Check system status (database, API, dataset)
    try:
        health_status = get_system_health()
    except Exception as e:
        health_status = {
            "db_connected": False,
            "db_type": "Unknown",
            "db_message": str(e),
            "api_online": False,
            "api_mode": "In-Process Engine",
        }

    # 3. Render persistent sidebar and obtain selected page
    selected_page = render_sidebar(system_status=health_status)

    # 4. Route to page renderer
    try:
        if selected_page == "Overview":
            render_overview_page()
        elif selected_page == "Job Market Intelligence":
            render_job_market_page()
        elif selected_page == "Salary Analytics":
            render_salary_analytics_page()
        elif selected_page == "Salary Prediction":
            render_salary_prediction_page()
        elif selected_page == "Resume Analyzer":
            render_resume_analyzer_page()
        elif selected_page == "Skill Gap Analysis":
            render_skill_gap_page()
        elif selected_page == "Company Intelligence":
            import importlib
            import dashboard.pages.company_intelligence as p_comp_intel
            importlib.reload(p_comp_intel)
            p_comp_intel.render_company_intelligence_page()
        elif selected_page == "Data Quality Report":
            render_data_quality_page()
        elif selected_page == "About & Methodology":
            render_about_page()
        else:
            render_overview_page()

    except Exception as err:
        st.error(f"Application view error: {type(err).__name__} - {str(err)}")
        render_disclaimer()


if __name__ == "__main__":
    main()
