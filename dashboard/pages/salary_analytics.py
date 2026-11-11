"""
Module: dashboard.pages.salary_analytics
Description: NIRNAYA In-depth compensation analytics page operating strictly on the verified
salary modeling dataset (17,559 records) with LPA consistency and quartile spreads.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import pandas as pd

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading, render_alert
from dashboard.components.metric_cards import render_kpi_row
from dashboard.components.charts import (
    create_bar_chart,
    create_histogram,
    create_box_plot,
)
from dashboard.components.tables import render_styled_table
from dashboard.data_loader import (
    load_salary_dataset,
    get_cached_salary_analytics,
)


def render_salary_analytics_page() -> None:
    """Renders the comprehensive NIRNAYA salary analytics page."""
    render_header(
        title="NIRNAYA Verified Compensation Analytics",
        subtitle="Empirical salary benchmarks derived strictly from 17,559 disclosed, high-integrity tech compensation records.",
        tag="Verified Salary (LPA)",
    )

    df_salary = load_salary_dataset()
    salary_stats = get_cached_salary_analytics()

    range_stats = salary_stats.get("salary_range_analysis", {})
    total_records = range_stats.get("total_salary_records", len(df_salary))
    median_lpa = range_stats.get("median_lpa", 10.50)
    mean_lpa = range_stats.get("mean_lpa", 11.83)
    p25_lpa = range_stats.get("p25_lpa", 6.50)
    p75_lpa = range_stats.get("p75_lpa", 16.00)
    std_lpa = range_stats.get("std_lpa", 7.42)

    # 1. Salary KPI Row with NIRNAYA Accents
    kpi_cards = [
        {
            "title": "Verified Sample Size",
            "value": f"{total_records:,}",
            "subtitle": "58.0% market coverage",
            "accent": "#F59E51",  # Orange
        },
        {
            "title": "Market Median",
            "value": f"₹{median_lpa:.2f} LPA",
            "subtitle": "50th percentile benchmark",
            "accent": "#F8D299",  # Light Orange
        },
        {
            "title": "Market Mean",
            "value": f"₹{mean_lpa:.2f} LPA",
            "subtitle": "Parametric tech average",
            "accent": "#804A8A",  # Primary Purple
        },
        {
            "title": "Interquartile Range",
            "value": f"₹{p25_lpa:.1f} – ₹{p75_lpa:.1f}",
            "subtitle": "P25 to P75 middle 50%",
            "accent": "#FB923C",  # Tangerine
        },
        {
            "title": "Standard Deviation",
            "value": f"± ₹{std_lpa:.2f} LPA",
            "subtitle": "Compensation spread",
            "accent": "#A85CB5",  # Bright Purple
        },
    ]
    render_kpi_row(kpi_cards)

    render_alert(
        "<strong>Integrity Assurance:</strong> Salary benchmarks exclude all missing, zero, negative, and inverted records. "
        "All calculations strictly utilize the verified <code>salary_mid_lpa</code> variable in INR Lakhs Per Annum (LPA).",
        alert_type="info",
    )

    # 2. Role-wise Compensation Hierarchy
    render_section_heading("Compensation Hierarchy by Canonical Role", icon="🏆")

    top_paying = salary_stats.get("top_paying_roles", [])
    top_paying_df = pd.DataFrame(top_paying)

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        if not top_paying_df.empty:
            fig_role_sal = create_bar_chart(
                data=top_paying_df,
                x="median_lpa",
                y="role",
                title="Median Salary by Canonical Role (INR LPA)",
                horizontal=True,
                height=420,
            )
            st.plotly_chart(fig_role_sal, use_container_width=True)

    with col2:
        if not top_paying_df.empty:
            display_top = top_paying_df[["rank", "role", "median_lpa", "mean_lpa", "job_count"]].rename(
                columns={
                    "rank": "Rank",
                    "role": "Role",
                    "median_lpa": "Median (LPA)",
                    "mean_lpa": "Mean (LPA)",
                    "job_count": "Verified Postings",
                }
            )
            render_styled_table(
                display_top,
                title="Ranked Role Compensation Table",
                max_rows=12,
            )

    # 3. Experience Progression & Seniority Tiers
    render_section_heading("Salary Progression Across Seniority Tiers", icon="📈")

    col3, col4 = st.columns(2)

    with col3:
        exp_order = ["Fresher", "Junior", "Mid-level", "Senior", "Lead"]
        sub_exp_df = df_salary[df_salary["experience_level"].isin(exp_order)]
        fig_box = create_box_plot(
            sub_exp_df,
            x="experience_level",
            y="salary_mid_lpa",
            title="Compensation Spread Across Seniority Levels (LPA)",
            height=380,
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with col4:
        exp_summary = salary_stats.get("salary_by_experience", {})
        exp_records = []
        for tier in exp_order:
            if tier in exp_summary:
                data = exp_summary[tier]
                exp_records.append({
                    "Seniority Tier": tier,
                    "Median (LPA)": f"₹{data['median_lpa']:.2f}",
                    "Mean (LPA)": f"₹{data['mean_lpa']:.2f}",
                    "P25 – P75 (LPA)": f"₹{data['p25_lpa']:.1f} – ₹{data['p75_lpa']:.1f}",
                    "Sample Count": f"{data['count']:,}",
                })
        render_styled_table(
            pd.DataFrame(exp_records),
            title="Seniority Tier Benchmark Table",
            max_rows=10,
        )

    # 4. City & Work Mode Breakdown
    render_section_heading("Geographic & Work Mode Compensation Variations", icon="🏙️")

    col5, col6 = st.columns(2)

    with col5:
        city_sal = salary_stats.get("salary_by_city", {})
        city_records = []
        for city, stats in city_sal.items():
            city_records.append({"City": city, "Median (LPA)": stats["median_lpa"], "Mean (LPA)": stats["mean_lpa"], "Count": stats["count"]})
        city_df = pd.DataFrame(city_records).sort_values(by="Median (LPA)", ascending=False).head(10)
        if not city_df.empty:
            fig_city_sal = create_bar_chart(
                data=city_df,
                x="City",
                y="Median (LPA)",
                title="Top 10 Cities by Median Compensation (LPA)",
                horizontal=False,
                height=360,
            )
            st.plotly_chart(fig_city_sal, use_container_width=True)

    with col6:
        wm_sal = salary_stats.get("salary_by_work_mode", {})
        wm_records = []
        for wm, stats in wm_sal.items():
            wm_records.append({"Work Mode": wm, "Median (LPA)": stats["median_lpa"], "Mean (LPA)": stats["mean_lpa"], "Postings": stats["count"]})
        wm_df = pd.DataFrame(wm_records)
        if not wm_df.empty:
            fig_wm_sal = create_bar_chart(
                data=wm_df,
                x="Work Mode",
                y="Median (LPA)",
                title="Median Salary by Work Mode (LPA)",
                horizontal=False,
                height=360,
            )
            st.plotly_chart(fig_wm_sal, use_container_width=True)

    # 5. Salary Distribution Curve
    render_section_heading("Overall Salary Distribution Curve", icon="📊")
    fig_hist = create_histogram(
        series=df_salary["salary_mid_lpa"],
        title="Distribution of Tech Compensation (Right-Skewed LPA Distribution)",
        x_title="Compensation (INR Lakhs Per Annum)",
        nbins=40,
        height=340,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    render_disclaimer()
