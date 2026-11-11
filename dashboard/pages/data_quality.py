"""
Module: dashboard.pages.data_quality
Description: NIRNAYA Data Quality and Governance page documenting cleaning pipelines, duplicate removal,
missing value treatments, and salary reconciliation.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import pandas as pd
import textwrap

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading, render_alert
from dashboard.components.metric_cards import render_kpi_row
from dashboard.components.tables import render_styled_table
from dashboard.data_loader import load_market_dataset, load_salary_dataset


def render_data_quality_page() -> None:
    """Renders the NIRNAYA data quality and preprocessing verification report."""
    render_header(
        title="NIRNAYA Data Quality & Integrity Audit",
        subtitle="Transparent documentation of data cleaning, deduplication, missing value strategies, and salary dataset reconciliation.",
        tag="Data Governance",
    )

    df_market = load_market_dataset()
    df_salary = load_salary_dataset()

    # 1. Pipeline Funnel KPIs with NIRNAYA Accents
    kpi_cards = [
        {
            "title": "Raw Input Records",
            "value": "31,150",
            "subtitle": "Initial messy CSV ingestion",
            "accent": "#804A8A",  # Primary Purple
        },
        {
            "title": "Exact Duplicates Removed",
            "value": "900",
            "subtitle": "Identical row deduplication",
            "accent": "#F59E51",  # Orange
        },
        {
            "title": "Cleaned Market Postings",
            "value": f"{len(df_market):,}",
            "subtitle": "Preserved for market EDA",
            "accent": "#F8D299",  # Light Orange
        },
        {
            "title": "Salary Modeling Records",
            "value": f"{len(df_salary):,}",
            "subtitle": "17,559 verified records",
            "accent": "#34D399",  # Emerald
        },
        {
            "title": "Excluded Salary Outliers",
            "value": "546",
            "subtitle": "Negative/inverted anomalies",
            "accent": "#FB923C",  # Tangerine
        },
    ]
    render_kpi_row(kpi_cards)

    render_alert(
        "<strong>Strict Separation of Market and Salary Datasets:</strong> Records lacking salary disclosure (12,145 postings) "
        "were intentionally retained for role demand, geographic, and skill intelligence rather than imputed blindly, "
        "preventing artificial variance deflation.",
        alert_type="info",
    )

    # 2. Salary Reconciliation Audit (The 546 Records)
    render_section_heading("Salary Dataset Reconciliation Audit (Step 2 vs Step 3)", icon="🔍")

    reconciliation_data = [
        {"Pipeline Stage": "1. Raw Total Records", "Record Count": "31,150", "Percentage": "100.0%", "Disposition / Action": "Initial uncleaned input file"},
        {"Pipeline Stage": "2. Exact Duplicates Purged", "Record Count": "-900", "Percentage": "-2.89%", "Disposition / Action": "Exact row duplicates removed"},
        {"Pipeline Stage": "3. Cleaned Job Market Dataset", "Record Count": "30,250", "Percentage": "97.11%", "Disposition / Action": "Full dataset for Market Overview & Skill Intelligence"},
        {"Pipeline Stage": "4. Missing Salary Disclosures", "Record Count": "-12,145", "Percentage": "-38.99%", "Disposition / Action": "Preserved in market dataset, omitted from regression"},
        {"Pipeline Stage": "5. Initial Salary Records", "Record Count": "18,105", "Percentage": "58.12%", "Disposition / Action": "Postings with numeric salary fields"},
        {"Pipeline Stage": "6. Outlier & Inverted Bounds Purged", "Record Count": "-546", "Percentage": "-1.75%", "Disposition / Action": "Removed negative bounds, min > max, or extreme outliers"},
        {"Pipeline Stage": "7. Final Verified Salary Model Set", "Record Count": "17,559", "Percentage": "56.37%", "Disposition / Action": "High-integrity regression training and validation set"},
    ]
    render_styled_table(
        pd.DataFrame(reconciliation_data),
        title="Full Data Cleaning Funnel & Salary Reconciliation Table",
        max_rows=10,
    )

    # 3. Column-by-Column Cleaning Strategy
    render_section_heading("Column-Level Preprocessing & Normalization Protocol", icon="🛠️")

    cleaning_strategies = [
        {"Column": "job_title", "Cleaning Strategy": "Stripped whitespace, lowercased, and mapped 40+ variations into 12 canonical roles via regex lookup.", "Missing Treatment": "0 missing. Unmapped titles mapped to clean title casing."},
        {"Column": "company_name", "Cleaning Strategy": "Unified casing, removed trailing whitespace and corporate punctuation.", "Missing Treatment": "0 missing. All records attributed to 16 recruiting companies."},
        {"Column": "city & state", "Cleaning Strategy": "Standardized 16 cities; cross-referenced state dictionary to impute missing state values.", "Missing Treatment": "Unknown cities labeled as 'Unknown' with state mapped accordingly."},
        {"Column": "experience_years", "Cleaning Strategy": "Parsed numeric strings and range representations into continuous float values.", "Missing Treatment": "Missing values imputed using role and seniority median."},
        {"Column": "experience_level", "Cleaning Strategy": "Normalized into 5 standard tiers: Fresher, Junior, Mid-level, Senior, Lead.", "Missing Treatment": "Inferred from experience_years where missing."},
        {"Column": "work_mode", "Cleaning Strategy": "Standardized to On-site, Hybrid, or Remote; fixed encoding anomalies.", "Missing Treatment": "Unknown work modes preserved as 'Unknown' (1.39%)."},
        {"Column": "skills_required", "Cleaning Strategy": "Punctuation stripping, alias replacement (e.g. 'py' -> 'Python'), deduplicated per posting.", "Missing Treatment": "Blank entries imputed with 'General Technical Skills'."},
        {"Column": "salary_min & max", "Cleaning Strategy": "Normalized into Lakhs Per Annum (LPA); validated non-negativity and min <= max.", "Missing Treatment": "Kept as NaN for market postings; excluded from salary training set."},
    ]
    render_styled_table(
        pd.DataFrame(cleaning_strategies),
        title="Column-by-Column Preprocessing Actions",
        max_rows=10,
    )

    # 4. Feature Space & Artifact Validation
    render_section_heading("Transformed Feature Matrix Specifications", icon="📦")

    feature_spec_html = textwrap.dedent("""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.25rem; line-height: 1.6; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
<div>
<h5 style="color: #F8D299; font-size: 0.95rem; margin: 0 0 0.25rem 0;">Numerical Features (2)</h5>
<span style="font-size: 0.85rem; color: #EFE4F5;"><code>experience_years</code>, <code>skill_count</code> (RobustScaled)</span>
</div>
<div>
<h5 style="color: #F59E51; font-size: 0.95rem; margin: 0 0 0.25rem 0;">Categorical Features (86)</h5>
<span style="font-size: 0.85rem; color: #EFE4F5;">One-Hot Encoded (Role, City, State, Experience, Work Mode, Edu, Size)</span>
</div>
<div>
<h5 style="color: #6EE7B7; font-size: 0.95rem; margin: 0 0 0.25rem 0;">Technical Skills (25)</h5>
<span style="font-size: 0.85rem; color: #EFE4F5;">MultiLabelBinarized binary indicators for top 25 skills</span>
</div>
</div>
<div style="margin-top: 1rem; border-top: 1px solid #681989; padding-top: 0.75rem; font-size: 0.825rem; color: #C8ABD6;">
Total Transformed Predictors: <strong style="color: #FFFFFF;">113 Features</strong> • Zero Data Leakage (Pipeline fitted exclusively on 14,047 training records).
</div>
</div>
""").strip()
    st.markdown(feature_spec_html, unsafe_allow_html=True)

    render_disclaimer()
