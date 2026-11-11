"""
Module: dashboard.components.filters
Description: Interactive multi-dimensional filtering bar for job market postings.
"""

import streamlit as st
import pandas as pd
from typing import Tuple, Dict, Any


def render_job_market_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Renders filter controls in an expandable panel and applies filtering to the dataset.

    Returns:
        Tuple of (filtered_df, active_filters_dict).
    """
    with st.expander("🔍 Interactive Market Filters & Dimensions", expanded=False):
        c1, c2, c3 = st.columns(3)

        with c1:
            roles = ["All Roles"] + sorted(df["clean_role"].dropna().unique().tolist())
            selected_role = st.selectbox("Job Role", options=roles, index=0)

            cities = ["All Cities"] + sorted(df["city"].dropna().unique().tolist())
            selected_city = st.selectbox("Hiring City", options=cities, index=0)

        with c2:
            states = ["All States"] + sorted(df["state"].dropna().unique().tolist()) if "state" in df.columns else ["All States"]
            selected_state = st.selectbox("State", options=states, index=0)

            exp_levels = ["All Levels"] + sorted(df["experience_level"].dropna().unique().tolist()) if "experience_level" in df.columns else ["All Levels"]
            selected_exp = st.selectbox("Experience Level", options=exp_levels, index=0)

        with c3:
            work_modes = ["All Modes"] + sorted(df["work_mode"].dropna().unique().tolist()) if "work_mode" in df.columns else ["All Modes"]
            selected_wm = st.selectbox("Work Mode", options=work_modes, index=0)

            emp_types = ["All Types"] + sorted(df["employment_type"].dropna().unique().tolist()) if "employment_type" in df.columns else ["All Types"]
            selected_emp = st.selectbox("Employment Type", options=emp_types, index=0)

    # Apply Filters
    filtered_df = df.copy()
    active_filters = {}

    if selected_role != "All Roles":
        filtered_df = filtered_df[filtered_df["clean_role"] == selected_role]
        active_filters["Role"] = selected_role

    if selected_city != "All Cities":
        filtered_df = filtered_df[filtered_df["city"] == selected_city]
        active_filters["City"] = selected_city

    if selected_state != "All States" and "state" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["state"] == selected_state]
        active_filters["State"] = selected_state

    if selected_exp != "All Levels" and "experience_level" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["experience_level"] == selected_exp]
        active_filters["Experience"] = selected_exp

    if selected_wm != "All Modes" and "work_mode" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["work_mode"] == selected_wm]
        active_filters["Work Mode"] = selected_wm

    if selected_emp != "All Types" and "employment_type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["employment_type"] == selected_emp]
        active_filters["Employment"] = selected_emp

    return filtered_df, active_filters

