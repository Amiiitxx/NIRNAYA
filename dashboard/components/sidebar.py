"""
Module: dashboard.components.sidebar
Description: NIRNAYA branded navigation controls, platform identity, and live system status indicators.
"""

import streamlit as st
import textwrap
from typing import Dict, Any, Optional

NAVIGATION_PAGES = [
    "Overview",
    "Job Market Intelligence",
    "Salary Analytics",
    "Salary Prediction",
    "Resume Analyzer",
    "Skill Gap Analysis",
    "Company Intelligence",
    "Data Quality Report",
    "About & Methodology",
]

NAVIGATION_ICONS = {
    "Overview": "📊",
    "Job Market Intelligence": "🌐",
    "Salary Analytics": "💰",
    "Salary Prediction": "🎯",
    "Resume Analyzer": "📄",
    "Skill Gap Analysis": "⚡",
    "Company Intelligence": "🏢",
    "Data Quality Report": "🛡️",
    "About & Methodology": "ℹ️",
}


def render_sidebar(system_status: Optional[Dict[str, Any]] = None) -> str:
    """
    Renders the persistent NIRNAYA sidebar with brand identity, page selection,
    and live infrastructure health indicators.
    """
    with st.sidebar:
        # NIRNAYA Brand Identity Header
        brand_html = textwrap.dedent("""
<div style="padding: 0.6rem 0 1.25rem 0; border-bottom: 1px solid #681989;">
<div style="display: flex; align-items: center; gap: 0.65rem;">
<div style="background: linear-gradient(135deg, #F59E51, #804A8A); width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.25rem; color: #FFFFFF; box-shadow: 0 4px 12px rgba(245, 158, 81, 0.4);">
N
</div>
<div>
<h2 style="font-size: 1.35rem; font-weight: 800; margin: 0; color: #FFFFFF; letter-spacing: 0.04em;">
NIRNAYA
</h2>
<span style="font-size: 0.72rem; color: #F8D299; font-weight: 600; display: block; line-height: 1.2;">Intelligence That Drives Decisions.</span>
</div>
</div>
<div style="font-size: 0.72rem; color: #C8ABD6; margin-top: 0.45rem; line-height: 1.3;">
An AI-Powered Career & Market Intelligence Platform
</div>
</div>
""").strip()
        st.markdown(brand_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

        # Navigation Section Heading
        nav_heading_html = textwrap.dedent("""
<p style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #F8D299; margin-bottom: 0.45rem;">
Navigation Menu
</p>
""").strip()
        st.markdown(nav_heading_html, unsafe_allow_html=True)

        # Check query parameters for initial selection if not set in session state
        default_idx = 0
        try:
            req_page = st.query_params.get("page", "").lower()
            if req_page:
                for idx, p in enumerate(NAVIGATION_PAGES):
                    if req_page in [p.lower(), p.lower().replace(" & ", "_").replace(" ", "_"), p.lower().split()[0]]:
                        default_idx = idx
                        break
        except Exception:
            pass

        # Radio navigation with icons
        display_options = [f"{NAVIGATION_ICONS[p]} {p}" for p in NAVIGATION_PAGES]
        selected_display = st.radio(
            "Select Section",
            options=display_options,
            index=default_idx,
            label_visibility="collapsed",
            key="nirnaya_navigation_radio",
        )

        # Map back to pure page name
        selected_page = selected_display.split(" ", 1)[1] if " " in selected_display else selected_display

        st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

        # Live Health & Dataset Status
        status_heading_html = textwrap.dedent("""
<p style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #F8D299; margin-bottom: 0.45rem;">
Platform Status
</p>
""").strip()
        st.markdown(status_heading_html, unsafe_allow_html=True)

        db_type = system_status.get("db_type", "SQLite") if system_status else "SQLite (Fallback)"
        db_online = system_status.get("db_connected", True) if system_status else True
        db_badge_color = "#34D399" if db_online else "#F59E51"
        db_label = f"Active ({db_type})" if db_online else "Fallback Mode"

        api_mode = system_status.get("api_mode", "In-Process Engine") if system_status else "In-Process Engine"

        status_card_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 10px; padding: 0.85rem; font-size: 0.775rem; box-shadow: 0 4px 14px rgba(0,0,0,0.3);">
<div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
<span style="color: #EFE4F5;">Market Postings:</span>
<strong style="color: #FFFFFF;">30,250 Active</strong>
</div>
<div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
<span style="color: #EFE4F5;">Salary Set:</span>
<strong style="color: #F8D299;">17,559 Verified</strong>
</div>
<div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
<span style="color: #EFE4F5;">Database:</span>
<span style="color: {db_badge_color}; font-weight: 700;">● {db_label}</span>
</div>
<div style="display: flex; justify-content: space-between;">
<span style="color: #EFE4F5;">Inference Engine:</span>
<strong style="color: #F59E51;">{api_mode}</strong>
</div>
</div>
""").strip()
        st.markdown(status_card_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Brand Footer
        footer_html = textwrap.dedent("""
<div style="text-align: center; color: #C8ABD6; font-size: 0.725rem; border-top: 1px solid #681989; padding-top: 0.75rem;">
<strong style="color: #FFFFFF; font-size: 0.8rem;">NIRNAYA</strong><br>
<span style="color: #F8D299;">Intelligence That Drives Decisions.</span><br>
<span style="color: #A88AB6; font-size: 0.68rem;">Release v1.0.0 • Python 3.10</span>
</div>
""").strip()
        st.markdown(footer_html, unsafe_allow_html=True)

    return selected_page
