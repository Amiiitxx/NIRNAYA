"""
Module: dashboard.pages.overview
Description: NIRNAYA Executive Overview page displaying macro KPIs, distributions, and strategic market insights.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import pandas as pd
import textwrap

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading
from dashboard.components.metric_cards import render_kpi_row
from dashboard.components.charts import (
    create_bar_chart,
    create_donut_chart,
)
from dashboard.data_loader import (
    get_cached_market_overview,
    get_cached_role_analytics,
    get_cached_city_analytics,
    get_cached_salary_analytics,
    get_cached_skill_intelligence,
)


def render_overview_page() -> None:
    """Renders the NIRNAYA executive overview dashboard page."""
    render_header(
        title="NIRNAYA Executive Market Overview",
        subtitle="Macro-level hiring intelligence, categorical distributions, and compensation benchmarks across India's technology ecosystem.",
        tag="Market Intelligence",
    )

    # 1. Fetch cached analytics
    overview = get_cached_market_overview()
    salary_stats = get_cached_salary_analytics()
    role_analytics = get_cached_role_analytics()
    city_analytics = get_cached_city_analytics()
    skill_intel = get_cached_skill_intelligence()

    total_postings = overview.get("total_job_postings", 30250)
    total_companies = overview.get("total_unique_companies", 16)
    total_roles = overview.get("total_job_roles", 12)
    total_cities = overview.get("total_cities", 16)

    salary_range = salary_stats.get("salary_range_analysis", {})
    median_sal = salary_range.get("median_lpa", 10.50)
    mean_sal = salary_range.get("mean_lpa", 11.83)

    # 2. Executive KPI Cards Row (NIRNAYA Purple & Orange Accents)
    kpi_cards = [
        {
            "title": "Total Job Postings",
            "value": f"{total_postings:,}",
            "subtitle": "Cleaned & validated postings",
            "tag": "Market Scope",
            "accent": "#F59E51",  # Orange
        },
        {
            "title": "Unique Companies",
            "value": f"{total_companies}",
            "subtitle": "Active corporate recruiters",
            "tag": "Employers",
            "accent": "#804A8A",  # Primary Purple
        },
        {
            "title": "Canonical Roles",
            "value": f"{total_roles}",
            "subtitle": "Specialized tech roles",
            "tag": "Taxonomy",
            "accent": "#F8D299",  # Light Orange
        },
        {
            "title": "Hiring Hubs (Cities)",
            "value": f"{total_cities}",
            "subtitle": "Metro & Tier-2 centers",
            "tag": "Geographies",
            "accent": "#FB923C",  # Tangerine
        },
        {
            "title": "Verified Median Salary",
            "value": f"₹{median_sal:.2f} LPA",
            "subtitle": "50th percentile benchmark",
            "tag": "Median (LPA)",
            "accent": "#F59E51",  # Orange
        },
        {
            "title": "Verified Average Salary",
            "value": f"₹{mean_sal:.2f} LPA",
            "subtitle": "Parametric tech mean",
            "tag": "Mean (LPA)",
            "accent": "#A85CB5",  # Bright Purple
        },
    ]
    render_kpi_row(kpi_cards)

    # 3. Macro Visualizations Grid
    render_section_heading("Market Volume & Distribution Overview", icon="📈")

    col1, col2 = st.columns(2)

    with col1:
        # Job postings by role
        roles_dict = role_analytics.get("postings_by_role", {})
        fig_roles = create_bar_chart(
            data=roles_dict,
            x="Count",
            y="Role",
            title="Job Postings by Canonical Tech Role",
            horizontal=True,
            height=370,
        )
        st.plotly_chart(fig_roles, use_container_width=True)

    with col2:
        # Top 10 cities by hiring volume
        cities_dict = city_analytics.get("postings_by_city", {})
        top_10_cities = dict(list(cities_dict.items())[:10])
        fig_cities = create_bar_chart(
            data=top_10_cities,
            x="City",
            y="Postings",
            title="Top 10 Indian Tech Hiring Hubs",
            horizontal=False,
            height=370,
        )
        st.plotly_chart(fig_cities, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Work mode distribution
        wm_dist = overview.get("work_mode_distribution", {})
        fig_wm = create_donut_chart(
            data=wm_dist,
            names="Work Mode",
            values="Postings",
            title="Work Mode Distribution (On-site vs Hybrid vs Remote)",
            height=340,
        )
        st.plotly_chart(fig_wm, use_container_width=True)

    with col4:
        # Employment type distribution
        emp_dist = overview.get("employment_type_distribution", {})
        fig_emp = create_donut_chart(
            data=emp_dist,
            names="Employment Type",
            values="Postings",
            title="Employment Type Share (Full-time vs Contract)",
            height=340,
        )
        st.plotly_chart(fig_emp, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        # Experience level distribution
        exp_dist = overview.get("experience_level_distribution", {})
        fig_exp = create_bar_chart(
            data=exp_dist,
            x="Experience Level",
            y="Postings",
            title="Postings by Seniority Level",
            horizontal=False,
            height=350,
        )
        st.plotly_chart(fig_exp, use_container_width=True)

    with col6:
        # Top 10 In-Demand Skills
        top_skills = skill_intel.get("top_skills", [])[:10]
        skills_df = pd.DataFrame(top_skills)
        if not skills_df.empty:
            fig_skills = create_bar_chart(
                data=skills_df,
                x="demand_percentage",
                y="skill",
                title="Top 10 In-Demand Technical Skills (% of Postings)",
                horizontal=True,
                height=350,
            )
            st.plotly_chart(fig_skills, use_container_width=True)

    # 4. Data-Derived Strategic Insights
    render_section_heading("NIRNAYA Decision Intelligence Insights", icon="💡")

    insights_html = textwrap.dedent("""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.25rem; line-height: 1.65; box-shadow: 0 4px 16px rgba(0,0,0,0.3);">
<ul style="color: #EFE4F5; margin: 0; padding-left: 1.25rem;">
<li><strong style="color: #F8D299;">Balanced Cross-Role Hiring:</strong> The 30,250 postings demonstrate steady demand distributed across 12 canonical roles, with <code>Business Analyst</code> (2,604 postings, 8.61%), <code>BI Developer</code> (2,586, 8.55%), and <code>Cloud Engineer</code> (2,562, 8.47%) maintaining the highest volumes.</li>
<li><strong style="color: #F8D299;">Metropolitan Dominance with Tier-2 Growth:</strong> <code>Bengaluru</code> (2,117 postings, 7.00%), <code>Delhi NCR</code> (2,022, 6.68%), and <code>Hyderabad</code> (2,017, 6.67%) remain the primary hiring centers, alongside strong emerging activity in <code>Kochi</code> (2,005) and <code>Ahmedabad</code> (2,004).</li>
<li><strong style="color: #F8D299;">Flexible Work Arrangements:</strong> On-site roles represent <strong style="color: #F59E51;">42.26%</strong> of postings, while flexible arrangements account for <strong style="color: #F59E51;">56.35%</strong> (34.88% Hybrid + 21.47% Remote), reflecting modern tech workforce preferences.</li>
<li><strong style="color: #F8D299;">Specialized AI/ML Compensation Premium:</strong> Roles specializing in modern machine intelligence command market-leading compensation: <code>AI Engineer</code> (Median 15.08 LPA) and <code>MLOps Engineer</code> (Median 14.79 LPA) surpass classical engineering roles by over 50%.</li>
<li><strong style="color: #F8D299;">Core Skills Nexus:</strong> <code>Machine Learning</code> and <code>Python</code> co-occur in <strong style="color: #F59E51;">34.47%</strong> of all job postings, forming the single most critical technical foundation in the Indian software and data market.</li>
</ul>
</div>
""").strip()
    st.markdown(insights_html, unsafe_allow_html=True)

    render_disclaimer()
