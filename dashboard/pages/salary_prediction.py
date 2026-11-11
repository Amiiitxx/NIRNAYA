"""
Module: dashboard.pages.salary_prediction
Description: NIRNAYA interactive salary estimation calculator powered by the tuned XGBoost Regressor.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import textwrap
from typing import List, Dict

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading, render_alert
from dashboard.components.metric_cards import render_metric_card
from dashboard.data_loader import get_salary_predictor
from src.skill_analyzer import get_available_job_roles

# Standard City-State lookup for intuitive UX
CITY_STATE_MAP: Dict[str, str] = {
    "Ahmedabad": "Gujarat",
    "Bengaluru": "Karnataka",
    "Chennai": "Tamil Nadu",
    "Coimbatore": "Tamil Nadu",
    "Delhi NCR": "Delhi",
    "Gurugram": "Haryana",
    "Hyderabad": "Telangana",
    "Indore": "Madhya Pradesh",
    "Jaipur": "Rajasthan",
    "Kochi": "Kerala",
    "Kolkata": "West Bengal",
    "Mumbai": "Maharashtra",
    "Noida": "Uttar Pradesh",
    "Pune": "Maharashtra",
    "Thiruvananthapuram": "Kerala",
    "Unknown": "Unknown",
}

DEFAULT_SKILLS_BY_ROLE: Dict[str, List[str]] = {
    "AI Engineer": ["Python", "Machine Learning", "PyTorch", "FastAPI", "Docker"],
    "Data Scientist": ["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn"],
    "MLOps Engineer": ["Python", "Docker", "Kubernetes", "AWS", "Git", "FastAPI"],
    "Data Engineer": ["Python", "SQL", "Spark", "Docker", "AWS", "Hadoop"],
    "Cloud Engineer": ["AWS", "Docker", "Kubernetes", "Linux", "Git"],
    "Software Engineer": ["Python", "Java", "Docker", "Git", "SQL"],
    "BI Developer": ["Power BI", "SQL", "Tableau", "Excel", "Python"],
    "Data Analyst": ["SQL", "Excel", "Python", "Tableau", "Power BI"],
    "Business Analyst": ["SQL", "Excel", "Tableau", "Power BI"],
    "NLP Engineer": ["Python", "Machine Learning", "PyTorch", "FastAPI"],
    "Python Developer": ["Python", "Django", "Flask", "SQL", "Git"],
    "Machine Learning Engineer": ["Python", "Machine Learning", "Scikit-learn", "Docker", "PyTorch"],
}

ALL_CANONICAL_SKILLS: List[str] = [
    "AWS", "Airflow", "C++", "Computer Vision", "Docker", "Django", "Excel",
    "FastAPI", "Flask", "GCP", "Git", "Go", "GraphQL", "Hadoop", "Java",
    "JavaScript", "Kafka", "Kubernetes", "Linux", "Machine Learning", "MongoDB",
    "NLP", "NoSQL", "NumPy", "Pandas", "PostgreSQL", "Power BI", "PySpark",
    "PyTorch", "Python", "R", "React", "Rust", "SQL", "Scala", "Scikit-learn",
    "Spark", "Tableau", "TensorFlow", "TypeScript", "dbt"
]


def render_salary_prediction_page() -> None:
    """Renders the NIRNAYA interactive salary prediction calculator."""
    render_header(
        title="NIRNAYA AI-Powered Salary Prediction Engine",
        subtitle="Estimate benchmark market compensation for candidate profiles using our calibrated XGBoost Regressor.",
        tag="Machine Learning Inference",
    )

    predictor = get_salary_predictor()
    available_roles = get_available_job_roles()

    banner_html = textwrap.dedent("""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.15rem; margin-bottom: 1.5rem;">
<p style="margin: 0; color: #EFE4F5; font-size: 0.9rem; line-height: 1.5;">
Configure the candidate or position profile below. The inference pipeline applies 113 encoded features,
including experience progression, role alignment, geographic premiums, and skill bag-of-words.
</p>
</div>
""").strip()
    st.markdown(banner_html, unsafe_allow_html=True)

    # Prediction Form
    with st.form("nirnaya_salary_prediction_form"):
        r1_c1, r1_c2, r1_c3 = st.columns(3)

        with r1_c1:
            selected_role = st.selectbox(
                "Target Job Role *",
                options=available_roles,
                index=available_roles.index("Data Scientist") if "Data Scientist" in available_roles else 0,
            )

            experience_years = st.slider(
                "Experience (Years) *",
                min_value=0.0,
                max_value=25.0,
                value=4.0,
                step=0.5,
                help="Total full-time relevant professional tech experience.",
            )

        with r1_c2:
            cities_list = sorted(list(CITY_STATE_MAP.keys()))
            selected_city = st.selectbox(
                "Hiring Location (City) *",
                options=cities_list,
                index=cities_list.index("Bengaluru") if "Bengaluru" in cities_list else 0,
            )

            default_state = CITY_STATE_MAP.get(selected_city, "Karnataka")
            selected_state = st.text_input(
                "State (Derived)",
                value=default_state,
                disabled=True,
            )

        with r1_c3:
            work_mode = st.selectbox(
                "Work Mode *",
                options=["Hybrid", "On-site", "Remote"],
                index=0,
            )

            employment_type = st.selectbox(
                "Employment Type *",
                options=["Full-time", "Contract", "Internship", "Part-time"],
                index=0,
            )

        r2_c1, r2_c2 = st.columns(2)

        with r2_c1:
            education = st.selectbox(
                "Education Level",
                options=["Bachelor's", "Master's", "Doctorate", "High School / Diploma"],
                index=0,
            )

            company_size = st.selectbox(
                "Company Size",
                options=["Startup (1-50)", "Small (51-200)", "Mid-sized (201-500)", "Large (500-1000)", "Enterprise (1000+)"],
                index=2,
            )

        with r2_c2:
            industry = st.selectbox(
                "Industry Domain",
                options=["Technology / IT Services", "Financial Services", "Software Product", "E-commerce", "Healthcare", "Consulting"],
                index=0,
            )

            default_skills = DEFAULT_SKILLS_BY_ROLE.get(selected_role, ["Python", "SQL", "Git"])
            selected_skills = st.multiselect(
                "Technical Skills Acquired *",
                options=sorted(ALL_CANONICAL_SKILLS),
                default=[s for s in default_skills if s in ALL_CANONICAL_SKILLS],
                help="Select all relevant skills candidate brings to the position.",
            )

        submit_btn = st.form_submit_button("🚀 Compute Salary Benchmark", use_container_width=True)

    # Perform Prediction
    if submit_btn:
        if not selected_skills:
            st.error("⚠️ Please select at least one technical skill to calculate compensation.")
            return

        with st.spinner("Executing calibrated inference pipeline..."):
            try:
                result = predictor.predict(
                    job_title=selected_role,
                    experience_years=float(experience_years),
                    city=selected_city,
                    state=selected_state,
                    skills=selected_skills,
                    education=education,
                    work_mode=work_mode,
                    company_size=company_size,
                    industry=industry,
                    employment_type=employment_type,
                )

                pred_lpa = result["predicted_salary_lpa"]
                pred_inr = result["predicted_salary_annual_inr"]
                lower_lpa = result["lower_bound_lpa"]
                upper_lpa = result["upper_bound_lpa"]
                lower_inr = result["lower_bound_annual_inr"]
                upper_inr = result["upper_bound_annual_inr"]
                res_std = result.get("residual_std_lpa", 4.53)

                render_section_heading("Predicted Compensation Benchmark", icon="💰")

                # Metric display with NIRNAYA Accents
                m1, m2, m3 = st.columns(3)
                with m1:
                    render_metric_card(
                        title="Point Estimate",
                        value=f"₹{pred_lpa:.2f} LPA",
                        subtitle=f"≈ ₹{pred_inr:,} / year",
                        tag="Median Benchmark",
                        border_accent="#F59E51",  # Orange
                    )
                with m2:
                    render_metric_card(
                        title="90% Empirical Lower Bound",
                        value=f"₹{lower_lpa:.2f} LPA",
                        subtitle=f"≈ ₹{lower_inr:,} / year",
                        tag="-1.645 σ",
                        border_accent="#804A8A",  # Primary Purple
                    )
                with m3:
                    render_metric_card(
                        title="90% Empirical Upper Bound",
                        value=f"₹{upper_lpa:.2f} LPA",
                        subtitle=f"≈ ₹{upper_inr:,} / year",
                        tag="+1.645 σ",
                        border_accent="#F8D299",  # Light Orange
                    )

                # Diagnostic Summary
                summary_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.25rem; margin-top: 1rem; box-shadow: 0 4px 16px rgba(0,0,0,0.3);">
<h4 style="margin: 0 0 0.5rem 0; color: #FFFFFF; font-size: 1.05rem; font-weight: 700;">NIRNAYA Model Diagnostics & Confidence</h4>
<p style="color: #EFE4F5; font-size: 0.9rem; line-height: 1.6; margin: 0 0 0.6rem 0;">
A candidate with <strong style="color: #F8D299;">{experience_years} years</strong> experience for a <strong style="color: #F8D299;">{selected_role}</strong>
role in <strong style="color: #F8D299;">{selected_city}</strong> ({work_mode}) presenting <strong style="color: #F59E51;">{len(selected_skills)} technical skills</strong>
commands an estimated market benchmark of <strong style="color: #F59E51;">₹{pred_lpa:.2f} LPA</strong> (90% range: <strong style="color: #F8D299;">₹{lower_lpa:.2f} LPA – ₹{upper_lpa:.2f} LPA</strong>).
</p>
<div style="font-size: 0.775rem; color: #C8ABD6;">
Inference Model: <code style="color: #F8D299;">{result.get('model_name', 'Tuned XGBoost')}</code> • Version: <code style="color: #F8D299;">{result.get('model_version', '1.0.0')}</code> • Test Residual Std: <code style="color: #F8D299;">±{res_std} LPA</code>
</div>
</div>
""").strip()
                st.markdown(summary_html, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Inference error encountered: {str(e)}")

    render_disclaimer(predictor.disclaimer)
