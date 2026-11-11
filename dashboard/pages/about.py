"""
Module: dashboard.pages.about
Description: NIRNAYA Platform About, Methodology, Architectural Flow, and Responsible AI Governance page.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import textwrap

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading


def render_about_page() -> None:
    """Renders the comprehensive NIRNAYA project background and methodology page."""
    render_header(
        title="About NIRNAYA & System Methodology",
        subtitle="Architectural overview, machine learning methodology, privacy practices, and academic scope disclosure.",
        tag="Documentation & Ethics",
    )

    # 1. Platform Identity & Problem Statement
    render_section_heading("NIRNAYA Platform Identity & Mission", icon="🎯")

    intro_html = textwrap.dedent("""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.3rem; line-height: 1.65; margin-bottom: 1.25rem; box-shadow: 0 4px 16px rgba(0,0,0,0.3);">
<div style="display: flex; align-items: baseline; gap: 0.6rem; margin-bottom: 0.5rem;">
<h3 style="margin: 0; color: #FFFFFF; font-size: 1.4rem; font-weight: 800; letter-spacing: 0.02em;">NIRNAYA</h3>
<span style="color: #F59E51; font-weight: 700; font-size: 0.95rem;">• "Intelligence That Drives Decisions."</span>
</div>
<p style="color: #F8D299; font-size: 0.9rem; font-weight: 600; margin: 0 0 0.85rem 0;">
Brand Meaning: Decision, determination, and informed judgment. An AI-Powered Career & Market Intelligence Platform.
</p>
<p style="color: #EFE4F5; margin: 0 0 0.75rem 0; font-size: 0.9rem;">
<strong>The Industry Problem:</strong> Modern technology job markets in India suffer from opaque salary bands,
inconsistent role titles, ambiguous keyword requirements in job postings, and significant candidate skill gaps.
Job seekers lack objective compensation benchmarks and actionable learning pathways, while recruiters face noise in candidate qualification.
</p>
<p style="color: #C8ABD6; margin: 0; font-size: 0.865rem;">
NIRNAYA resolves this asymmetry by combining rigorous exploratory data analysis, calibrated regression modeling,
in-memory document parsing, dynamic skill gap scoring, and relational persistence into a unified, actionable decision layer.
</p>
</div>
""").strip()
    st.markdown(intro_html, unsafe_allow_html=True)

    # 2. Technology Stack & Architecture
    render_section_heading("Production Technology Architecture", icon="🏗️")

    tech_html = textwrap.dedent("""
<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.25rem;">
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.15rem; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
<h4 style="color: #F8D299; font-size: 1rem; font-weight: 700; margin: 0 0 0.5rem 0;">Core Machine Learning & Data Pipeline</h4>
<ul style="color: #EFE4F5; font-size: 0.865rem; padding-left: 1.2rem; margin: 0; line-height: 1.6;">
<li><strong>Modeling:</strong> XGBoost Regressor with <code>log1p(y)</code> target transformation</li>
<li><strong>Feature Pipeline:</strong> 113-dimension ColumnTransformer with RobustScaler and MultiLabelBinarizer</li>
<li><strong>Validation:</strong> 5-Fold Cross-Validation, Test MAE: <strong style="color: #F59E51;">2.25 LPA</strong>, R²: <strong style="color: #F59E51;">0.625</strong></li>
<li><strong>Analytics:</strong> Pandas 2.2, NumPy, Scikit-learn, Joblib</li>
</ul>
</div>
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.15rem; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
<h4 style="color: #F8D299; font-size: 1rem; font-weight: 700; margin: 0 0 0.5rem 0;">Backend Services & Interface</h4>
<ul style="color: #EFE4F5; font-size: 0.865rem; padding-left: 1.2rem; margin: 0; line-height: 1.6;">
<li><strong>REST API:</strong> FastAPI with Pydantic V2 response validation and OpenAPI docs</li>
<li><strong>Relational DB:</strong> PostgreSQL via SQLAlchemy 2.0 ORM with SQLite fallback</li>
<li><strong>NLP Parsing:</strong> PyMuPDF (fitz) with regex boundary taxonomy (42 skills)</li>
<li><strong>Dashboard UI:</strong> Streamlit 1.40+ with custom NIRNAYA purple and orange palette</li>
</ul>
</div>
</div>
""").strip()
    st.markdown(tech_html, unsafe_allow_html=True)

    # 3. Privacy, Security & Data Ethics
    render_section_heading("Privacy Principles & Responsible AI", icon="🛡️")

    ethics_html = textwrap.dedent("""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.25rem; line-height: 1.6; margin-bottom: 1.25rem; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
<div>
<h5 style="color: #6EE7B7; margin: 0 0 0.35rem 0; font-size: 0.95rem;">🔒 Zero PII Retention</h5>
<p style="font-size: 0.825rem; color: #EFE4F5; margin: 0; line-height: 1.5;">
Uploaded resumes are parsed entirely in-memory as temporary byte buffers. No names, contact details, or PDF files are written to disk.
</p>
</div>
<div>
<h5 style="color: #F59E51; margin: 0 0 0.35rem 0; font-size: 0.95rem;">📉 Uncertainty Bounds</h5>
<p style="font-size: 0.825rem; color: #EFE4F5; margin: 0; line-height: 1.5;">
Every salary prediction discloses empirical 90% confidence intervals (±1.645 × residual std) rather than deceptive single-number certainties.
</p>
</div>
<div>
<h5 style="color: #F8D299; margin: 0 0 0.35rem 0; font-size: 0.95rem;">⚖️ Fair Match Formula</h5>
<p style="font-size: 0.825rem; color: #EFE4F5; margin: 0; line-height: 1.5;">
Skill gap scoring weights skills according to real market demand percentage rather than arbitrary manual weightings.
</p>
</div>
</div>
</div>
""").strip()
    st.markdown(ethics_html, unsafe_allow_html=True)

    # 4. Mandatory Academic & Simulated Dataset Scope Disclosure
    render_section_heading("Academic Scope & Simulated Dataset Disclosure", icon="⚠️")

    disclosure_html = textwrap.dedent("""
<div style="background: rgba(245, 158, 81, 0.15); border-left: 4px solid #F59E51; border-radius: 8px; padding: 1rem 1.25rem; line-height: 1.6; margin-bottom: 1.5rem;">
<h4 style="color: #F8D299; margin: 0 0 0.45rem 0; font-size: 1.05rem; font-weight: 700;">Simulated Job Market Dataset Notice</h4>
<p style="color: #EFE4F5; font-size: 0.875rem; margin: 0 0 0.5rem 0;">
The underlying dataset (<code>india_job_market_messy_31150_records.csv</code>) is a synthetically generated benchmark
created for educational Data Science internships. While the statistical properties, salary ranges (LPA),
geographic distributions, and skill co-occurrences reflect realistic Indian tech industry patterns,
<strong>none of the individual postings, salary records, or recruiting companies represent live, verified corporate employment records.</strong>
</p>
<p style="color: #C8ABD6; font-size: 0.825rem; margin: 0;">
All statistics and predictions must be interpreted as demonstrating algorithmic and engineering workflows, not live macroeconomic labor statistics.
</p>
</div>
""").strip()
    st.markdown(disclosure_html, unsafe_allow_html=True)

    # 5. Project Creator Profile
    render_section_heading("Project Creator", icon="👨‍💻")

    creator_html = textwrap.dedent("""
<div style="background: #4B0968; border: 1px solid #681989; border-top: 3.5px solid #F59E51; border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);">
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 0.85rem;">
<div>
<div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: #F8D299; font-weight: 700; margin-bottom: 0.25rem;">Platform Creator & Lead Architect</div>
<h2 style="margin: 0; color: #FFFFFF; font-size: 1.75rem; font-weight: 800; letter-spacing: -0.01em;">Amiiitxx</h2>
<div style="color: #F59E51; font-size: 1.05rem; font-weight: 600; margin-top: 0.25rem;">Creator & Developer of NIRNAYA</div>
</div>
<span style="font-size: 0.75rem; font-weight: 700; background: rgba(245, 158, 81, 0.2); color: #F8D299; border: 1px solid #F59E51; padding: 4px 12px; border-radius: 9999px;">Project Lead</span>
</div>
<p style="color: #EFE4F5; font-size: 0.925rem; line-height: 1.65; margin: 0 0 1.25rem 0;">
Designed and developed as an AI-powered career and market intelligence platform using Data Science, Machine Learning, NLP, and modern web technologies.
</p>
<div>
<div style="font-size: 0.8rem; font-weight: 700; color: #F8D299; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.6rem;">Core Skills & Technologies</div>
<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
<span class="skill-badge skill-badge-essential">Python</span>
<span class="skill-badge skill-badge-essential">Data Science</span>
<span class="skill-badge skill-badge-essential">Machine Learning</span>
<span class="skill-badge skill-badge-essential">Data Analytics</span>
<span class="skill-badge skill-badge-essential">SQL</span>
<span class="skill-badge skill-badge-essential">FastAPI</span>
<span class="skill-badge skill-badge-essential">Streamlit</span>
</div>
</div>
</div>
""").strip()
    st.markdown(creator_html, unsafe_allow_html=True)

    render_disclaimer()
