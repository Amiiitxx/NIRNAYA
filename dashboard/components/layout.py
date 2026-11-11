"""
Module: dashboard.components.layout
Description: NIRNAYA layout utilities, custom CSS injection, headers, and disclaimer banners.
"""

import os
import textwrap
import streamlit as st
from typing import Optional

DEFAULT_DISCLAIMER = (
    "NIRNAYA Governance & Dataset Scope Disclaimer: All metrics, percentiles, salary models, and insights presented "
    "are derived from the platform's simulated benchmark dataset (30,250 cleaned postings across 16 Indian tech hubs). "
    "They represent statistical indicators for educational Data Science demonstration, not live macroeconomic statistics "
    "or contractual employment guarantees."
)


def apply_custom_css(css_path: Optional[str] = None) -> None:
    """
    Loads and injects custom CSS styling for the NIRNAYA purple and orange theme.
    """
    if css_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        css_path = os.path.join(base_dir, "assets", "style.css")

    if os.path.exists(css_path):
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except Exception:
            pass


def render_header(title: str, subtitle: str, tag: Optional[str] = None) -> None:
    """
    Renders standard styled page title and subtitle with NIRNAYA typography.
    """
    tag_html = f'<span class="skill-badge skill-badge-essential">{tag}</span>' if tag else ""
    html_block = textwrap.dedent(f"""
<div style="margin-bottom: 1.25rem;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<h1 class="page-title" style="margin: 0;">{title}</h1>
{tag_html}
</div>
<p class="page-subtitle">{subtitle}</p>
</div>
""").strip()
    st.markdown(html_block, unsafe_allow_html=True)


def render_alert(message: str, alert_type: str = "info") -> None:
    """
    Renders styled alert message box with NIRNAYA orange/purple accent.
    """
    css_class = f"saas-alert-{alert_type}" if alert_type in ["info", "warning"] else "saas-alert-info"
    html_block = textwrap.dedent(f"""
<div class="{css_class}">
{message}
</div>
""").strip()
    st.markdown(html_block, unsafe_allow_html=True)


def render_disclaimer(message: Optional[str] = None) -> None:
    """
    Renders NIRNAYA platform disclaimer footer banner.
    """
    text = message or DEFAULT_DISCLAIMER
    html_block = textwrap.dedent(f"""
<div class="saas-alert-disclaimer">
<strong style="color: #F59E51;">Disclaimer:</strong> {text}
</div>
""").strip()
    st.markdown(html_block, unsafe_allow_html=True)


def render_section_heading(title: str, icon: str = "") -> None:
    """
    Renders a styled section divider heading with NIRNAYA orange highlight.
    """
    prefix = f"{icon} " if icon else ""
    html_block = textwrap.dedent(f"""
<div style="margin: 1.6rem 0 0.9rem 0; border-bottom: 1px solid #681989; padding-bottom: 0.4rem;">
<h3 style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin: 0; letter-spacing: -0.01em;">
{prefix}{title}
</h3>
</div>
""").strip()
    st.markdown(html_block, unsafe_allow_html=True)
