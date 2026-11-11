"""
Module: dashboard.pages.skill_gap
Description: NIRNAYA Skill Gap Analysis page computing demand-weighted match scores and personalized learning pathways.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import pandas as pd
import textwrap
from typing import List, Dict

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading, render_alert
from dashboard.components.metric_cards import render_metric_card
from dashboard.components.charts import create_gauge_chart
from dashboard.components.tables import render_recommendation_cards
from dashboard.data_loader import load_market_dataset
from src.skill_analyzer import (
    get_available_job_roles,
    generate_skill_gap_report,
    get_role_required_skills,
)

# Standard skills fallback
CANONICAL_SKILLS: List[str] = [
    "AWS", "Airflow", "C++", "Computer Vision", "Docker", "Django", "Excel",
    "FastAPI", "Flask", "GCP", "Git", "Go", "GraphQL", "Hadoop", "Java",
    "JavaScript", "Kafka", "Kubernetes", "Linux", "Machine Learning", "MongoDB",
    "NLP", "NoSQL", "NumPy", "Pandas", "PostgreSQL", "Power BI", "PySpark",
    "PyTorch", "Python", "R", "React", "Rust", "SQL", "Scala", "Scikit-learn",
    "Spark", "Tableau", "TensorFlow", "TypeScript", "dbt"
]


def render_skill_gap_page() -> None:
    """Renders the NIRNAYA interactive skill gap analyzer and roadmap page."""
    render_header(
        title="NIRNAYA Skill Gap Analysis & Pathways",
        subtitle="Benchmark your technical capabilities against empirical role requirements derived from 30,250 job postings.",
        tag="Decision Intelligence",
    )

    df_market = load_market_dataset()
    available_roles = get_available_job_roles(df_market)

    # 1. Target Role & Skills Input Panel
    render_section_heading("Configure Target Role & Candidate Profile", icon="🎯")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        target_role = st.selectbox(
            "Select Target Job Role *",
            options=available_roles,
            index=available_roles.index("Data Scientist") if "Data Scientist" in available_roles else 0,
            help="Empirical benchmarks and priority thresholds will adjust to this target role.",
        )

        role_reqs = get_role_required_skills(target_role, df=df_market)
        essential_reqs = [s["skill"] for s in role_reqs if s["category"] == "Essential"]
        important_reqs = [s["skill"] for s in role_reqs if s["category"] == "Important"]

        st.caption(
            f"Role Benchmark: **{len(essential_reqs)} Essential** (≥50% demand) • "
            f"**{len(important_reqs)} Important** (25–50% demand)"
        )

    with col2:
        # Pre-populate from Resume Analyzer session state if available
        session_skills = st.session_state.get("candidate_skills", [])
        resume_name = st.session_state.get("resume_filename", None)

        default_skills = session_skills if session_skills else ["Python", "SQL", "Pandas"]
        if resume_name:
            st.info(f"📄 Loaded skills from uploaded resume: **{resume_name}**")

        candidate_skills = st.multiselect(
            "Candidate Technical Skills *",
            options=sorted(CANONICAL_SKILLS),
            default=[s for s in default_skills if s in CANONICAL_SKILLS],
            help="Select all technical skills acquired through education, projects, or work experience.",
        )

    if not candidate_skills:
        st.warning("⚠️ Please select or provide candidate skills to execute the gap analysis.")
        render_disclaimer()
        return

    # 2. Run Gap Analysis
    with st.spinner("Analyzing demand-weighted match formula and compiling learning recommendations..."):
        report = generate_skill_gap_report(candidate_skills, target_role, df=df_market)

    match_score = report["skill_match_score"]
    matched_skills = report["matched_skills"]
    missing_essential = report["missing_essential_skills"]
    missing_important = report["missing_important_skills"]
    missing_additional = report["missing_additional_skills"]
    recommendations = report["learning_recommendations"]

    # 3. Score & KPI Overview
    render_section_heading("Match Score & Alignment Diagnostics", icon="📊")

    gauge_col, kpi_col = st.columns([1.1, 1.9])

    with gauge_col:
        fig_gauge = create_gauge_chart(
            score=match_score,
            title="Demand-Weighted Match Score",
            height=280,
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with kpi_col:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card(
                title="Matched Skills",
                value=str(len(matched_skills)),
                subtitle=f"of {report['total_required_skills']} required",
                border_accent="#10B981",  # Emerald
            )
        with m2:
            render_metric_card(
                title="Missing Essential",
                value=str(len(missing_essential)),
                subtitle="≥50% market demand",
                border_accent="#F59E51",  # Orange
            )
        with m3:
            render_metric_card(
                title="Missing Important",
                value=str(len(missing_important)),
                subtitle="25–50% market demand",
                border_accent="#F8D299",  # Light Orange
            )
        with m4:
            render_metric_card(
                title="Missing Additional",
                value=str(len(missing_additional)),
                subtitle="<25% market demand",
                border_accent="#804A8A",  # Primary Purple
            )

        render_alert(
            "<strong>Mathematical Weighting:</strong> Match score represents <code>(Matched Skill Demand / Total Role Skill Demand) × 100</code>. "
            "Essential skills with high market prevalence contribute significantly more weight than niche competencies.",
            alert_type="info",
        )

    # 4. Matched vs Missing Badges
    render_section_heading("Detailed Skill Breakdown", icon="🔍")

    b_col1, b_col2 = st.columns(2)

    with b_col1:
        heading_matched = textwrap.dedent("""
<h4 style="color: #6EE7B7; font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem;">
✅ Matched Skills
</h4>
""").strip()
        st.markdown(heading_matched, unsafe_allow_html=True)
        if matched_skills:
            badges_html = " ".join([f"<span class='skill-badge skill-badge-matched'>{s}</span>" for s in matched_skills])
            box_matched = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 10px; padding: 1rem;">
{badges_html}
</div>
""").strip()
            st.markdown(box_matched, unsafe_allow_html=True)
        else:
            st.info("No matching skills found for this role.")

    with b_col2:
        heading_missing = textwrap.dedent("""
<h4 style="color: #F8D299; font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem;">
❌ Missing Essential Skills
</h4>
""").strip()
        st.markdown(heading_missing, unsafe_allow_html=True)
        if missing_essential:
            badges_html = " ".join([f"<span class='skill-badge skill-badge-essential'>{s}</span>" for s in missing_essential])
            box_missing = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 10px; padding: 1rem;">
{badges_html}
</div>
""").strip()
            st.markdown(box_missing, unsafe_allow_html=True)
        else:
            st.success("🎉 Excellent! All essential skills for this role are satisfied.")

    # 5. Personalized Learning Pathways
    render_section_heading("Personalized Upskilling & Portfolio Roadmap", icon="🚀")
    render_recommendation_cards(recommendations)

    render_disclaimer(
        "Skill match percentage represents alignment with job posting keyword demand. It does not evaluate coding proficiency, "
        "architectural depth, or interviewing performance and does not constitute a hiring guarantee."
    )
