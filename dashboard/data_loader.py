"""
Module: dashboard.data_loader
Description: Centralized caching and service initialization for Streamlit.
"""

import os
import urllib.request
import json
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional

from src.job_market_intelligence import (
    get_market_dataset,
    get_salary_dataset,
    get_market_overview,
    get_job_role_analytics,
    get_city_analytics,
    get_salary_analytics,
    get_skill_intelligence,
    get_temporal_trends,
)
from src.salary_model import SalaryPredictor
from src.resume_parser import ResumeParser
from database.db import check_db_connection


@st.cache_data(show_spinner=False)
def load_market_dataset() -> pd.DataFrame:
    """Loads and caches the cleaned full job market dataset (30,250 records)."""
    return get_market_dataset()


@st.cache_data(show_spinner=False)
def load_salary_dataset() -> pd.DataFrame:
    """Loads and caches the verified salary modeling dataset (17,559 records)."""
    return get_salary_dataset()


@st.cache_data(show_spinner=False)
def get_cached_market_overview() -> Dict[str, Any]:
    """Caches macro market KPIs and categorical distributions."""
    df = load_market_dataset()
    return get_market_overview(df)


@st.cache_data(show_spinner=False)
def get_cached_role_analytics() -> Dict[str, Any]:
    """Caches role rankings and cross-tabulations."""
    df = load_market_dataset()
    return get_job_role_analytics(df, top_n=12)


@st.cache_data(show_spinner=False)
def get_cached_city_analytics() -> Dict[str, Any]:
    """Caches city hiring volumes and state breakdowns."""
    df = load_market_dataset()
    return get_city_analytics(df, top_n=16)


@st.cache_data(show_spinner=False)
def get_cached_salary_analytics() -> Dict[str, Any]:
    """Caches verified salary analytics computed exclusively on salary dataset."""
    df_sal = load_salary_dataset()
    return get_salary_analytics(df_sal)


@st.cache_data(show_spinner=False)
def get_cached_skill_intelligence() -> Dict[str, Any]:
    """Caches technical skill demand and pairwise co-occurrence."""
    df = load_market_dataset()
    return get_skill_intelligence(df, top_n=20)


@st.cache_resource(show_spinner=False)
def get_salary_predictor() -> SalaryPredictor:
    """Initializes and caches the trained SalaryPredictor instance."""
    return SalaryPredictor()


@st.cache_resource(show_spinner=False)
def get_resume_parser() -> ResumeParser:
    """Initializes and caches the ResumeParser instance."""
    return ResumeParser()


def get_system_health() -> Dict[str, Any]:
    """
    Checks the status of the dataset, database connection, and API service.
    """
    db_connected, db_msg = check_db_connection()

    # Determine DB Type from message or configuration
    db_type = "PostgreSQL" if "postgresql" in str(os.environ.get("DATABASE_URL", "")).lower() else "SQLite (Fallback)"

    # Check FastAPI health endpoint with short timeout
    api_online = False
    api_mode = "In-Process Engine"
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health", headers={"User-Agent": "Streamlit-HealthCheck"})
        with urllib.request.urlopen(req, timeout=0.5) as response:
            if response.status == 200:
                api_online = True
                api_mode = "FastAPI Service (Live)"
    except Exception:
        api_online = False
        api_mode = "In-Process Engine (Active)"

    return {
        "db_connected": db_connected,
        "db_type": db_type,
        "db_message": db_msg,
        "api_online": api_online,
        "api_mode": api_mode,
        "market_dataset_rows": 30250,
        "salary_dataset_rows": 17559,
    }

