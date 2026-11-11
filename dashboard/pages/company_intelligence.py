"""
Module: dashboard.pages.company_intelligence
Description: NIRNAYA Company-Specific Skill Gap Analysis & Career Improvement Page.
Empowers candidates to analyze specific company job postings, compare candidate resumes,
receive tailored 30-60-90 day roadmaps, and obtain evidence-based resume improvements.
Guarantees clean HTML rendering via zero-indent formatting.
"""

import io
import textwrap
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    create_bar_chart,
    create_donut_chart,
    create_gauge_chart,
)
from dashboard.components.layout import (
    render_alert,
    render_disclaimer,
    render_header,
    render_section_heading,
)
from dashboard.components.metric_cards import render_kpi_row
from src.company_intelligence.company_analyzer import analyze_company_target
from src.company_intelligence.validators import validate_url_security
from src.resume_parser import (
    extract_sections_from_text,
    extract_skills_from_text,
    extract_text_from_pdf,
)

SAMPLE_JOB_SPEC = """Company: InnovateTech AI Solutions
Role: Senior Machine Learning Engineer
Location: Bengaluru, Karnataka (Hybrid)
Experience: 3-5 years of relevant industry experience
Education: B.Tech / B.E. / M.Tech in Computer Science, Data Science, or related field

About the Role:
We are looking for an experienced Senior Machine Learning Engineer to design and deploy scalable predictive intelligence models across our distributed cloud platforms.

Requirements (Must Have):
- 3+ years of production experience in Python and SQL.
- Strong hands-on background in Machine Learning, Pandas, and Scikit-learn.
- Experience building scalable asynchronous REST APIs using FastAPI or Flask.
- Production containerization and deployment using Docker and Git.

Preferred Qualifications (Nice to Have):
- Experience with AWS (EC2, S3, ECS) and Kubernetes orchestration.
- Familiarity with PyTorch or TensorFlow for Deep Learning architectures.
- Knowledge of PostgreSQL and Redis caching layers.
- Agile/Scrum team development practices.
"""


def render_company_intelligence_page() -> None:
    """Renders the comprehensive Company Intelligence & Career Improvement page."""
    render_header(
        title="NIRNAYA Company Intelligence & Skill Gap Engine",
        subtitle="Target-specific job requirement extraction, candidate skill gap comparison, personalized career roadmaps, and resume enhancement studio.",
        tag="Company Intelligence",
    )

    # -------------------------------------------------------------------------
    # 1. Job / Company Ingestion Hub
    # -------------------------------------------------------------------------
    render_section_heading("Job Posting & Company Target Ingestion", icon="🎯")

    ingestion_html = textwrap.dedent("""
<div style="background: #4B0968; border: 1px solid #681989; border-left: 4px solid #F59E51; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
<div style="color: #FFFFFF; font-weight: 700; font-size: 0.95rem; margin-bottom: 0.25rem;">Target-Specific Evaluation Hub</div>
<p style="color: #EFE4F5; font-size: 0.865rem; margin: 0; line-height: 1.55;">
Analyze requirements directly from any target employer. Provide a public URL or paste the job description text below,
then connect your resume to generate an objective match matrix, targeted learning roadmaps, and resume enhancement guidance.
</p>
</div>
""").strip()
    st.markdown(ingestion_html, unsafe_allow_html=True)

    tab_direct, tab_company, tab_linkedin, tab_manual = st.tabs([
        "🔗 Direct Job Posting URL",
        "🏢 Company Website URL",
        "💼 LinkedIn Job URL",
        "📝 Manual Job Description",
    ])

    input_mode = "manual"
    target_content = ""

    # Support URL query params for testing and direct deep-linking
    query_target = st.query_params.get("target_url", "")
    query_auto_analyze = st.query_params.get("auto_analyze", "").lower() == "true"

    with tab_direct:
        st.markdown("<p style='font-size: 0.85rem; color: #F8D299;'>Enter a public job posting URL (e.g. Greenhouse, Lever, Workday, career portal):</p>", unsafe_allow_html=True)
        url_direct = st.text_input(
            "Direct Job URL",
            value=query_target if ("jobs.lever" in query_target or "greenhouse" in query_target) else "",
            placeholder="https://jobs.lever.co/company-name/job-id",
            key="url_direct_input",
            label_visibility="collapsed",
        )
        if url_direct.strip():
            input_mode = "direct_job_url"
            target_content = url_direct.strip()

    with tab_company:
        st.markdown("<p style='font-size: 0.85rem; color: #F8D299;'>Enter a company website or public career page URL:</p>", unsafe_allow_html=True)
        url_company = st.text_input(
            "Company URL",
            value=query_target if ("careers" in query_target or "company.com" in query_target or "google.com" in query_target) else "",
            placeholder="https://company.com/careers",
            key="url_company_input",
            label_visibility="collapsed",
        )
        if url_company.strip():
            input_mode = "company_url"
            target_content = url_company.strip()

    with tab_linkedin:
        st.markdown(
            "<p style='font-size: 0.85rem; color: #F8D299;'>"
            "Enter a public LinkedIn job URL. If protected by login or auth-wall, automatic fallback is provided:"
            "</p>",
            unsafe_allow_html=True,
        )
        url_linkedin = st.text_input(
            "LinkedIn Job URL",
            placeholder="https://www.linkedin.com/jobs/view/1234567890",
            key="url_linkedin_input",
            label_visibility="collapsed",
        )
        if url_linkedin.strip():
            input_mode = "linkedin_url"
            target_content = url_linkedin.strip()

    with tab_manual:
        st.markdown("<p style='font-size: 0.85rem; color: #F8D299;'>Paste job description text directly (guaranteed 100% available offline):</p>", unsafe_allow_html=True)
        col_load, _ = st.columns([2, 5])
        with col_load:
            if st.button("📋 Load Sample Machine Learning Spec", use_container_width=True):
                st.session_state["company_intel_manual_text"] = SAMPLE_JOB_SPEC

        manual_text = st.text_area(
            "Manual Job Description",
            value=st.session_state.get("company_intel_manual_text", ""),
            height=200,
            placeholder="Paste role requirements, responsibilities, and qualifications here...",
            key="company_intel_manual_text",
            label_visibility="collapsed",
        )
        if manual_text.strip():
            input_mode = "manual_text"
            target_content = manual_text.strip()

    # -------------------------------------------------------------------------
    # Candidate Resume & Profile Connection
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    render_section_heading("Candidate Resume & Profile Connection", icon="📄")

    col_res1, col_res2 = st.columns([1, 1])

    extracted_resume_skills: List[str] = []
    resume_raw_text: str = ""

    with col_res1:
        st.markdown("<p style='font-size: 0.85rem; color: #F8D299; font-weight: 600;'>Option A: Upload Resume PDF</p>", unsafe_allow_html=True)
        uploaded_pdf = st.file_uploader(
            "Upload Resume PDF",
            type=["pdf"],
            key="company_intel_resume_uploader",
            help="Processed entirely in-memory using PyMuPDF. Zero files or PII written to disk.",
        )
        if uploaded_pdf is not None:
            try:
                pdf_bytes = uploaded_pdf.getvalue() if hasattr(uploaded_pdf, "getvalue") else uploaded_pdf.read()
                if hasattr(uploaded_pdf, "seek"):
                    uploaded_pdf.seek(0)
                extracted_text, page_count, warnings, status = extract_text_from_pdf(pdf_bytes)
                if status == "SUCCESS" and extracted_text.strip():
                    resume_raw_text = extracted_text
                    extracted_resume_skills = extract_skills_from_text(extracted_text)
                    st.success(
                        f"Parsed {page_count}-page resume. "
                        f"Extracted {len(extracted_resume_skills)} skills: {', '.join(extracted_resume_skills[:8])}..."
                    )
                elif status == "WARNING":
                    resume_raw_text = extracted_text
                    extracted_resume_skills = extract_skills_from_text(extracted_text) if extracted_text else []
                    warn_detail = "; ".join(warnings) if warnings else "Partial or image-only PDF detected."
                    st.warning(f"Resume text warning: {warn_detail}")
                    if extracted_resume_skills:
                        st.info(f"Extracted {len(extracted_resume_skills)} skills: {', '.join(extracted_resume_skills[:8])}...")
                else:  # status == "FAILED"
                    err_detail = "; ".join(warnings) if warnings else "Unable to parse resume PDF."
                    st.warning(f"Could not extract text: {err_detail}")
            except Exception as e:
                st.error(f"Error parsing PDF: {str(e)}")

    with col_res2:
        st.markdown("<p style='font-size: 0.85rem; color: #F8D299; font-weight: 600;'>Option B: Confirmed Candidate Skills</p>", unsafe_allow_html=True)
        default_candidate_skills = extracted_resume_skills if extracted_resume_skills else [
            "Python", "SQL", "Machine Learning", "Scikit-learn", "Pandas", "FastAPI"
        ]
        candidate_skills_confirmed = st.multiselect(
            "Select or add candidate skills",
            options=sorted(list(set(default_candidate_skills + [
                "Python", "SQL", "Machine Learning", "Deep Learning", "FastAPI", "Flask", "Django",
                "Docker", "Kubernetes", "AWS", "GCP", "Azure", "PostgreSQL", "MySQL", "MongoDB",
                "Pandas", "NumPy", "Scikit-learn", "PyTorch", "TensorFlow", "React", "Node.js", "Git"
            ]))),
            default=default_candidate_skills,
            help="Verify or manually add confirmed skills for evaluation.",
        )

    # Trigger Evaluation Button
    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2, _ = st.columns([2, 2, 3])
    with btn_col1:
        button_clicked = st.button("🚀 Analyze Target Requirements", type="primary", use_container_width=True)
        analyze_clicked = button_clicked or (query_auto_analyze and bool(target_content))

    if not analyze_clicked and "company_intel_analysis_result" not in st.session_state:
        st.info("Select an input method above, provide job details, and click 'Analyze Target Requirements'.")
        render_disclaimer()
        return

    # Execute Analysis if clicked
    if analyze_clicked:
        if not target_content:
            st.error("Please provide a valid Job Posting URL, Company URL, or paste the Job Description text.")
            return

        with st.spinner("Extracting structured job requirements and evaluating candidate profile..."):
            result = analyze_company_target(
                input_content=target_content,
                candidate_skills=candidate_skills_confirmed,
                resume_text=resume_raw_text,
                source_type=input_mode,
            )
            st.session_state["company_intel_analysis_result"] = result

    result = st.session_state.get("company_intel_analysis_result")
    if not result:
        return

    if not result["success"]:
        st.error(f"Analysis Failed: {result.get('error_message')}")
        if result.get("is_login_walled"):
            st.info("💡 Tip: Copy the job text from the web page and paste it into the 'Manual Job Description' tab.")
        render_disclaimer()
        return

    job_reqs = result["job_requirements"]
    comparison = result["comparison_result"]
    recs = result["recommendations"]
    resume_impr = result["resume_improvements"]
    roadmap = result["roadmap"]

    # Check for insufficient job requirement data (e.g. generic company homepages or blank requirements)
    has_sufficient_reqs = result.get("has_sufficient_requirements", True) and bool(job_reqs.get("all_skills"))
    if not has_sufficient_reqs:
        comp_name = job_reqs.get("company_name", "Not specified")

        render_alert(
            "Insufficient job requirement data. Please provide a specific job posting URL or paste the job description manually.",
            alert_type="warning",
        )

        if comp_name not in {"Not specified", ""}:
            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
            render_section_heading("Target Company Context", icon="🏢")
            homepage_card_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-left: 4px solid #F59E51; border-radius: 10px; padding: 1.25rem; margin-top: 0.5rem; margin-bottom: 1.25rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
<div>
<span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #F8D299; font-weight: 700;">Verified Hiring Organization</span>
<h3 style="font-size: 1.4rem; color: #FFFFFF; margin: 0.2rem 0; font-weight: 800;">{comp_name}</h3>
</div>
<span style="background: rgba(245, 158, 81, 0.2); color: #F8D299; border: 1px solid #F59E51; padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700;">
Company Homepage / Career Portal
</span>
</div>
<p style="color: #EFE4F5; font-size: 0.9rem; line-height: 1.6; margin: 0 0 0.75rem 0;">
The provided URL is a general company homepage or careers portal landing page. It does not contain specific job role qualifications, required skills, or experience criteria.
</p>
<div style="background: rgba(58, 3, 83, 0.6); border-radius: 8px; padding: 0.85rem 1rem; border: 1px dashed #804A8A;">
<p style="color: #F8D299; font-size: 0.85rem; font-weight: 700; margin: 0 0 0.25rem 0;">👉 Recommended Next Steps:</p>
<ul style="color: #FFFFFF; font-size: 0.85rem; margin: 0; padding-left: 1.2rem; line-height: 1.5;">
<li>Browse to a specific job opening on the {comp_name} careers site (e.g. Software Engineer, Data Scientist).</li>
<li>Copy the direct job posting URL and paste it into the <b>Direct Job Posting URL</b> tab.</li>
<li>Alternatively, copy the full job description text and paste it directly into the <b>Manual Job Description</b> tab.</li>
</ul>
</div>
</div>
""").strip()
            st.markdown(homepage_card_html, unsafe_allow_html=True)

        render_disclaimer()
        return

    # -------------------------------------------------------------------------
    # 2. Extracted Job Dossier
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    render_section_heading("Extracted Job Dossier & Company Context", icon="🏢")

    dossier_cards = [
        {"title": "Target Company", "value": job_reqs.get("company_name", "Not specified"), "subtitle": "Hiring Organization", "tag": "Employer", "accent": "#F59E51"},
        {"title": "Target Role", "value": job_reqs.get("job_title", "Not specified"), "subtitle": "Position Title", "tag": "Role", "accent": "#804A8A"},
        {"title": "Work Location", "value": job_reqs.get("location", "Not specified"), "subtitle": "Office / Remote", "tag": "Location", "accent": "#F8D299"},
        {"title": "Required Experience", "value": job_reqs.get("experience_required", "Not specified"), "subtitle": "Seniority Tier", "tag": "Experience", "accent": "#FB923C"},
        {"title": "Education Criteria", "value": job_reqs.get("education_required", "Not specified"), "subtitle": "Academic Benchmark", "tag": "Degree", "accent": "#A85CB5"},
    ]
    render_kpi_row(dossier_cards)

    # -------------------------------------------------------------------------
    # 3. Extracted Skills Taxonomy
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
    render_section_heading("Job Skill Classification & Domain Breakdown", icon="🏷️")

    col_tax1, col_tax2 = st.columns([1, 1])
    with col_tax1:
        st.markdown("<p style='font-size: 0.9rem; color: #F59E51; font-weight: 700;'>Mandatory Requirements (Must-Have)</p>", unsafe_allow_html=True)
        mand_skills = job_reqs.get("mandatory_skills", [])
        if mand_skills:
            badges_html = " ".join([f"<span class='skill-badge skill-badge-essential'>{s}</span>" for s in mand_skills])
            st.markdown(f"<div style='margin-bottom: 0.85rem;'>{badges_html}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size: 0.825rem; color: #C8ABD6;'>No explicit mandatory skills isolated.</p>", unsafe_allow_html=True)

        st.markdown("<p style='font-size: 0.9rem; color: #F8D299; font-weight: 700;'>Preferred / Bonus Skills (Nice-to-Have)</p>", unsafe_allow_html=True)
        pref_skills = job_reqs.get("preferred_skills", [])
        if pref_skills:
            badges_html = " ".join([f"<span class='skill-badge skill-badge-important'>{s}</span>" for s in pref_skills])
            st.markdown(f"<div>{badges_html}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size: 0.825rem; color: #C8ABD6;'>No explicit preferred skills isolated.</p>", unsafe_allow_html=True)

    with col_tax2:
        st.markdown("<p style='font-size: 0.9rem; color: #FFFFFF; font-weight: 700;'>Technical Domain Distribution</p>", unsafe_allow_html=True)
        cat_counts = {domain: len(skills) for domain, skills in job_reqs.get("categorized_skills", {}).items() if skills}
        if cat_counts:
            fig_domain = create_donut_chart(cat_counts, names="Domain", values="Skills", title="Skill Domain Breakdown", height=240)
            st.plotly_chart(fig_domain, use_container_width=True)

    # -------------------------------------------------------------------------
    # 4. Company vs Candidate Comparison Matrix
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
    render_section_heading("Company vs. Candidate Requirement Comparison Matrix", icon="⚖️")

    matrix_data = comparison.get("comparison_matrix", [])
    if matrix_data:
        df_matrix = pd.DataFrame(matrix_data)
        # Format column headers
        df_display = df_matrix.rename(columns={
            "skill": "Required Technical Skill",
            "requirement_type": "Requirement Tier",
            "status": "Candidate Status",
            "priority": "Remediation Priority",
            "reason": "Evaluation Note",
        })

        col_filter1, col_filter2 = st.columns([1, 1])
        with col_filter1:
            status_filter = st.multiselect(
                "Filter by Candidate Status",
                options=["Matched", "Missing", "Partially Matched", "Needs Verification"],
                default=["Matched", "Missing", "Partially Matched", "Needs Verification"],
                key="matrix_status_filter",
            )
        with col_filter2:
            priority_filter = st.multiselect(
                "Filter by Priority",
                options=["High", "Medium", "Low"],
                default=["High", "Medium", "Low"],
                key="matrix_priority_filter",
            )

        df_filtered = df_display[
            df_display["Candidate Status"].isin(status_filter) &
            df_display["Remediation Priority"].isin(priority_filter)
        ]
        st.dataframe(df_filtered, use_container_width=True, height=280)

    # -------------------------------------------------------------------------
    # 5. Skill Gap Analytics & Match Score
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
    render_section_heading("Target Role Match Analytics & Gap Severity", icon="📊")

    col_gauge, col_stats = st.columns([1, 1])

    with col_gauge:
        score = comparison.get("match_score", 0.0)
        fig_gauge = create_gauge_chart(score, title="Company Technical Alignment Score", height=280)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_stats:
        status_counts = {
            "Matched": len(comparison.get("matched_skills", [])),
            "Missing (Mandatory)": len(comparison.get("missing_mandatory_skills", [])),
            "Missing (Preferred)": len(comparison.get("missing_preferred_skills", [])),
            "Partially Matched": len(comparison.get("partially_matched_skills", [])),
        }
        fig_bar = create_bar_chart(
            status_counts,
            x="Status",
            y="Count",
            title="Skill Gap Severity Breakdown",
            horizontal=False,
            height=280,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    render_alert(comparison.get("disclaimer", ""), alert_type="info")

    # -------------------------------------------------------------------------
    # 6. Targeted Resume Improvement Studio
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
    render_section_heading("Tailored Resume Improvement Studio (Google XYZ Model)", icon="✍️")

    col_kw, col_xyz = st.columns([1, 1])

    with col_kw:
        st.markdown("<p style='font-size: 0.9rem; color: #F59E51; font-weight: 700;'>ATS Keyword Optimization Guidance</p>", unsafe_allow_html=True)
        kw_suggestions = resume_impr.get("keyword_suggestions", [])
        if kw_suggestions:
            for item in kw_suggestions[:5]:
                card_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-left: 3px solid #F59E51; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.6rem;">
<div style="font-size: 0.825rem; font-weight: 700; color: #F8D299;">{item['keyword']} <span style="font-size: 0.72rem; color: #C8ABD6; float: right;">{item['importance']}</span></div>
<p style="font-size: 0.785rem; color: #EFE4F5; margin: 0.25rem 0 0 0; line-height: 1.45;">{item['action']}</p>
</div>
""").strip()
                st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.success("Great keyword alignment! All primary technical keywords are present.")

    with col_xyz:
        st.markdown("<p style='font-size: 0.9rem; color: #F8D299; font-weight: 700;'>Action-Oriented Bullet Point Restructuring</p>", unsafe_allow_html=True)
        rewrites = resume_impr.get("bullet_rewrites", [])
        if rewrites:
            for item in rewrites[:3]:
                card_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.6rem;">
<div style="font-size: 0.8rem; font-weight: 700; color: #F8D299; margin-bottom: 0.2rem;">Skill Focus: {item['skill_focus']}</div>
<div style="font-size: 0.75rem; color: #C8ABD6; text-decoration: line-through; margin-bottom: 0.35rem;">Weak: "{item['weak_pattern_example']}"</div>
<div style="font-size: 0.8rem; color: #6EE7B7; font-weight: 600; line-height: 1.45; background: rgba(16,185,129,0.1); padding: 0.4rem 0.6rem; border-radius: 6px;">
Recommended: "{item['recommended_xyz_structure']}"
</div>
</div>
""").strip()
                st.markdown(card_html, unsafe_allow_html=True)

    render_alert(resume_impr.get("anti_hallucination_guarantee", ""), alert_type="warning")

    # -------------------------------------------------------------------------
    # 7. Personalized 30-60-90 Day Career Roadmap
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
    render_section_heading("Actionable 30–60–90 Day Preparation Pathway", icon="🗺️")

    st.markdown(f"<p style='font-size: 0.865rem; color: #EFE4F5; margin-bottom: 1rem;'>{roadmap.get('summary', '')}</p>", unsafe_allow_html=True)

    tab_30, tab_60, tab_90 = st.tabs([
        "📅 Month 1: 30-Day Foundation",
        "⚙️ Month 2: 60-Day Integration",
        "🚀 Month 3: 90-Day Capstone & Interview",
    ])

    def render_phase_card(phase_data: Dict[str, Any]):
        focus = ", ".join(phase_data.get("focus_skills", []))
        timeframe = phase_data.get("timeframe", "")
        commitment = phase_data.get("estimated_weekly_commitment", "")

        header_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-top: 3px solid #F59E51; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
<div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF;">{phase_data.get('phase_name', '')}</div>
<span style="font-size: 0.75rem; font-weight: 700; background: rgba(245,158,81,0.2); color: #F8D299; padding: 3px 10px; border-radius: 9999px;">{timeframe}</span>
</div>
<div style="font-size: 0.825rem; color: #F8D299;"><strong>Priority Target Skills:</strong> {focus}</div>
<div style="font-size: 0.785rem; color: #C8ABD6; margin-top: 0.2rem;">Commitment: {commitment}</div>
</div>
""").strip()
        st.markdown(header_html, unsafe_allow_html=True)

        for m in phase_data.get("weekly_milestones", []):
            deliv_items = "".join([f"<li>{d}</li>" for d in m.get("deliverables", [])])
            m_html = textwrap.dedent(f"""
<div style="background: rgba(75, 9, 104, 0.5); border: 1px solid rgba(128, 74, 138, 0.3); border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 0.75rem;">
<div style="font-size: 0.865rem; font-weight: 700; color: #F59E51; margin-bottom: 0.3rem;">{m.get('week', '')}: {m.get('title', '')}</div>
<ul style="color: #EFE4F5; font-size: 0.8rem; margin: 0 0 0.5rem 0; padding-left: 1.2rem; line-height: 1.5;">
{deliv_items}
</ul>
<div style="font-size: 0.785rem; color: #F8D299;"><strong>Weekly Deliverable:</strong> {m.get('assignment', '')}</div>
</div>
""").strip()
            st.markdown(m_html, unsafe_allow_html=True)

    with tab_30:
        render_phase_card(roadmap.get("plan_30_days", {}))

    with tab_60:
        render_phase_card(roadmap.get("plan_60_days", {}))

    with tab_90:
        render_phase_card(roadmap.get("plan_90_days", {}))

    render_disclaimer()
