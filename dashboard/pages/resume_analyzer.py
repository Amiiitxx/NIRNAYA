"""
Module: dashboard.pages.resume_analyzer
Description: NIRNAYA Resume PDF parsing and skill extraction engine operating in-memory with strict PII privacy.
Guarantees clean HTML rendering without raw tags or CommonMark code block leaks.
"""

import streamlit as st
import textwrap
from typing import List, Dict

from dashboard.components.layout import render_header, render_disclaimer, render_section_heading, render_alert
from dashboard.components.metric_cards import render_metric_card
from dashboard.data_loader import get_resume_parser


def render_resume_analyzer_page() -> None:
    """Renders the NIRNAYA resume PDF upload and skill extraction interface."""
    render_header(
        title="NIRNAYA Resume Skill Extraction Engine",
        subtitle="Extract technical skill profiles and resume sections from PDF resumes in real time with zero persistent storage.",
        tag="NLP & Document AI",
    )

    parser = get_resume_parser()

    # Privacy Guarantee Card
    privacy_html = textwrap.dedent("""
<div style="background: rgba(16, 185, 129, 0.15); border-left: 4px solid #10B981; border-radius: 8px; padding: 0.95rem 1.25rem; margin-bottom: 1.25rem;">
<strong style="color: #6EE7B7; font-size: 0.95rem;">🔒 Strict Privacy & Ephemeral In-Memory Processing:</strong>
<span style="color: #EFE4F5; font-size: 0.865rem; display: block; margin-top: 0.25rem; line-height: 1.45;">
Uploaded resumes are parsed in-memory as byte streams. No files, personal contact information,
names, or extracted text are persisted to disk or logged.
</span>
</div>
""").strip()
    st.markdown(privacy_html, unsafe_allow_html=True)

    # PDF Uploader
    uploaded_file = st.file_uploader(
        "Upload Candidate Resume (PDF format, max 10 MB)",
        type=["pdf"],
        help="Upload text-based PDF resumes generated from Word, LaTeX, Google Docs, or LinkedIn.",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > 10.0:
            st.error(f"❌ File size exceeds 10 MB limit ({file_size_mb:.2f} MB). Please upload a smaller PDF.")
            return

        with st.spinner("NIRNAYA Document AI: Parsing text layers and mapping skill taxonomy..."):
            result = parser.parse(file_bytes, filename=file_name)

        status = result.get("extraction_status", "SUCCESS")
        extracted_skills = result.get("extracted_skills", [])
        skill_count = result.get("skill_count", 0)
        sections = result.get("sections", {})
        warnings = result.get("warnings", [])

        # Status & Warnings
        if status == "FAILED":
            st.error(f"❌ Extraction failed: {warnings[0] if warnings else 'Unknown document error.'}")
            return
        elif status == "WARNING":
            for w in warnings:
                render_alert(f"⚠️ {w}", alert_type="warning")

        # Metric Summary Cards
        render_section_heading("Extraction Overview", icon="📊")
        m1, m2, m3 = st.columns(3)
        with m1:
            render_metric_card(
                title="Document Status",
                value=status,
                subtitle=file_name,
                tag="Validated",
                border_accent="#10B981" if status == "SUCCESS" else "#F59E51",
            )
        with m2:
            render_metric_card(
                title="Technical Skills",
                value=str(skill_count),
                subtitle="Canonical skills mapped",
                tag="Taxonomy",
                border_accent="#F59E51",
            )
        with m3:
            detected_sec_count = sum(1 for v in sections.values() if v.strip())
            render_metric_card(
                title="Sections Segmented",
                value=f"{detected_sec_count} of {len(sections)}",
                subtitle="Standard resume sections",
                tag="Heuristic",
                border_accent="#804A8A",
            )

        # Extracted Skills Pills
        render_section_heading("Detected Technical Skills", icon="⚡")
        if extracted_skills:
            badges_html = " ".join([f"<span class='skill-badge skill-badge-matched'>{s}</span>" for s in extracted_skills])
            skills_box_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
{badges_html}
</div>
""").strip()
            st.markdown(skills_box_html, unsafe_allow_html=True)

            # Action to send to Skill Gap Analysis
            if st.button("➡️ Forward Extracted Skills to NIRNAYA Skill Gap Analysis", use_container_width=True):
                st.session_state["candidate_skills"] = extracted_skills
                st.session_state["resume_filename"] = file_name
                st.success(f"✅ Successfully transferred {skill_count} skills to Skill Gap Analysis module!")
        else:
            st.info("No standardized technical skills from our taxonomy were detected in this document.")

        # Section Details in Expanders
        render_section_heading("Detected Resume Sections", icon="📑")
        for sec_name, sec_content in sections.items():
            has_content = bool(sec_content.strip())
            badge = "✅ Found" if has_content else "⚪ Empty / Not Detected"
            with st.expander(f"{sec_name.title()} Section ({badge})", expanded=has_content and sec_name == "skills"):
                if has_content:
                    st.text_area(f"{sec_name}_text", value=sec_content, height=140, disabled=True, label_visibility="collapsed")
                else:
                    st.caption(f"No text detected for {sec_name} section heading.")

    else:
        st.info("👆 Upload a PDF resume above to view automated skill extraction, section segmentation, and taxonomy mapping.")

    render_disclaimer()
