"""
Module: dashboard.pages.job_market
Description: NIRNAYA Deep-dive Job Market Intelligence page with multi-dimensional filtering,
rankings, geographic breakdowns, and skill co-occurrence matrices.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import pandas as pd
import textwrap
from collections import Counter

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading
from dashboard.components.filters import render_job_market_filters
from dashboard.components.metric_cards import render_kpi_row
from dashboard.components.charts import (
    create_bar_chart,
    create_donut_chart,
)
from dashboard.components.tables import render_styled_table
from dashboard.data_loader import (
    load_market_dataset,
    get_cached_skill_intelligence,
)


def render_job_market_page() -> None:
    """Renders the comprehensive NIRNAYA job market intelligence page."""
    render_header(
        title="NIRNAYA Job Market Intelligence & Analytics",
        subtitle="Explore role demand volumes, geographic concentrations, and technical skill networks across Indian hiring markets.",
        tag="Market Exploration",
    )

    df_market = load_market_dataset()

    # 1. Interactive Filters
    filtered_df, active_filters = render_job_market_filters(df_market)

    # 2. Filter Summary KPIs
    active_count = len(filtered_df)
    total_count = len(df_market)
    pct_filtered = round((active_count / total_count) * 100, 1)

    unique_companies = filtered_df["company_name"].nunique() if "company_name" in filtered_df.columns else 0
    unique_cities = filtered_df["city"].nunique() if "city" in filtered_df.columns else 0
    unique_roles = filtered_df["clean_role"].nunique() if "clean_role" in filtered_df.columns else 0

    kpi_cards = [
        {
            "title": "Filtered Postings",
            "value": f"{active_count:,}",
            "subtitle": f"{pct_filtered}% of market volume",
            "accent": "#F59E51",  # Orange
        },
        {
            "title": "Represented Companies",
            "value": f"{unique_companies}",
            "subtitle": "Active corporate recruiters",
            "accent": "#804A8A",  # Primary Purple
        },
        {
            "title": "Active Hiring Hubs",
            "value": f"{unique_cities}",
            "subtitle": "Cities meeting criteria",
            "accent": "#F8D299",  # Light Orange
        },
        {
            "title": "Specialized Roles",
            "value": f"{unique_roles}",
            "subtitle": "Canonical tech roles",
            "accent": "#FB923C",  # Tangerine
        },
    ]
    render_kpi_row(kpi_cards)

    if filtered_df.empty:
        st.warning("⚠️ No job postings match the specified filter criteria. Please broaden your selection.")
        render_disclaimer()
        return

    # 3. Role & Geography Deep Dive
    render_section_heading("Role Rankings & Geographic Breakdown", icon="📍")

    col1, col2 = st.columns(2)

    with col1:
        role_counts = filtered_df["clean_role"].value_counts().head(10).to_dict()
        fig_roles = create_bar_chart(
            data=role_counts,
            x="Postings",
            y="Role",
            title="Top In-Demand Roles in Selected Subset",
            horizontal=True,
            height=380,
        )
        st.plotly_chart(fig_roles, use_container_width=True)

    with col2:
        city_counts = filtered_df["city"].value_counts().head(10).to_dict()
        fig_cities = create_bar_chart(
            data=city_counts,
            x="City",
            y="Postings",
            title="Top Hiring Cities in Selected Subset",
            horizontal=False,
            height=380,
        )
        st.plotly_chart(fig_cities, use_container_width=True)

    # 4. State Distribution & Work Arrangements
    col3, col4 = st.columns(2)

    with col3:
        if "state" in filtered_df.columns:
            state_counts = filtered_df["state"].value_counts().head(8).to_dict()
            fig_states = create_bar_chart(
                data=state_counts,
                x="State",
                y="Postings",
                title="State-wise Hiring Distribution (Top 8)",
                horizontal=False,
                height=350,
            )
            st.plotly_chart(fig_states, use_container_width=True)

    with col4:
        wm_counts = filtered_df["work_mode"].value_counts().to_dict()
        fig_wm = create_donut_chart(
            data=wm_counts,
            names="Work Mode",
            values="Postings",
            title="Work Mode Breakdown",
            height=350,
        )
        st.plotly_chart(fig_wm, use_container_width=True)

    # 5. Technical Skill Demand & Co-occurrence
    render_section_heading("Technical Skill Demand & Co-occurrence Networks", icon="⚡")

    # Calculate skill frequency in filtered set
    skill_counts = Counter()
    for s_str in filtered_df["skills_required_clean"].dropna():
        unique_s = set(s.strip() for s in str(s_str).split(",") if s.strip())
        for s in unique_s:
            skill_counts[s] += 1

    top_subset_skills = []
    for skill, count in skill_counts.most_common(12):
        pct = round((count / len(filtered_df)) * 100, 2)
        top_subset_skills.append({"skill": skill, "job_count": int(count), "demand_percentage": pct})

    skills_df = pd.DataFrame(top_subset_skills)

    col5, col6 = st.columns([1, 1])

    with col5:
        if not skills_df.empty:
            fig_sub_skills = create_bar_chart(
                data=skills_df,
                x="demand_percentage",
                y="skill",
                title="Top Required Skills in Filtered Postings (%)",
                horizontal=True,
                height=400,
            )
            st.plotly_chart(fig_sub_skills, use_container_width=True)

    with col6:
        # Top Co-occurring skill pairs from overall intelligence
        skill_intel = get_cached_skill_intelligence()
        co_pairs = skill_intel.get("co_occurring_skills", [])[:10]
        co_df = pd.DataFrame(co_pairs)
        if not co_df.empty:
            display_co = co_df[["skill_pair", "co_occurrence_count", "co_occurrence_percentage"]].rename(
                columns={
                    "skill_pair": "Skill Pair Synergy",
                    "co_occurrence_count": "Co-occurrence Count",
                    "co_occurrence_percentage": "Co-occurrence Share (%)",
                }
            )
            render_styled_table(
                display_co,
                title="Top Market-Wide Skill Co-occurrences (Synergies)",
                max_rows=10,
            )

    # 6. Sample Postings Table
    render_section_heading("Filtered Job Postings Explorer", icon="📋")
    cols_to_show = [c for c in ["job_id", "job_title", "clean_role", "company_name", "city", "work_mode", "experience_level", "skills_required_clean"] if c in filtered_df.columns]
    render_styled_table(
        filtered_df[cols_to_show].rename(
            columns={
                "job_id": "Job ID",
                "job_title": "Title",
                "clean_role": "Canonical Role",
                "company_name": "Company",
                "city": "City",
                "work_mode": "Mode",
                "experience_level": "Level",
                "skills_required_clean": "Required Skills",
            }
        ),
        max_rows=10,
    )

    render_disclaimer()
