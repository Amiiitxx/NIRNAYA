"""
Module: dashboard.components.tables
Description: NIRNAYA styled table rendering and learning recommendation cards.
Guarantees clean HTML rendering by eliminating CommonMark markdown indentation blocks.
"""

import streamlit as st
import pandas as pd
import textwrap
from typing import List, Dict, Any, Optional


def render_styled_table(
    df: pd.DataFrame,
    title: Optional[str] = None,
    max_rows: int = 15,
) -> None:
    """
    Renders a styled DataFrame with clean column headers and pagination limits.
    """
    if title:
        title_html = textwrap.dedent(f"""
<h4 style="color: #FFFFFF; font-size: 1.05rem; font-weight: 700; margin-bottom: 0.5rem;">
{title}
</h4>
""").strip()
        st.markdown(title_html, unsafe_allow_html=True)

    if df.empty:
        st.info("No matching records found for the selected criteria.")
        return

    display_df = df.head(max_rows)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
    if len(df) > max_rows:
        st.caption(f"Showing top {max_rows} of {len(df):,} total records.")


def render_recommendation_cards(recommendations: List[Dict[str, Any]]) -> None:
    """
    Renders structured learning recommendation cards with NIRNAYA prioritized badges.
    """
    if not recommendations:
        st.success("🎉 You possess all required technical skills for this role! No critical skill gaps identified.")
        return

    for rec in recommendations:
        skill = rec.get("skill", "Skill")
        priority = rec.get("priority", "Additional")
        pct = rec.get("demand_percentage", 0.0)
        action = rec.get("suggested_learning_action", "")
        project = rec.get("suggested_project_practice", "")

        badge_class = "skill-badge-additional"
        if priority == "Essential":
            badge_class = "skill-badge-essential"
        elif priority == "Important":
            badge_class = "skill-badge-important"

        card_html = textwrap.dedent(f"""
<div style="background: #4B0968; border: 1px solid #681989; border-radius: 12px; padding: 1.1rem; margin-bottom: 0.85rem; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.55rem;">
<div style="display: flex; align-items: center; gap: 0.55rem;">
<span style="font-weight: 800; font-size: 1.1rem; color: #FFFFFF;">{skill}</span>
<span class="skill-badge {badge_class}">{priority} Priority</span>
</div>
<span style="font-size: 0.825rem; color: #F8D299;">Market Demand: <strong style="color: #F59E51;">{pct}%</strong></span>
</div>
<div style="font-size: 0.885rem; color: #EFE4F5; margin-bottom: 0.4rem; line-height: 1.5;">
<strong style="color: #F8D299;">📚 Learning Action:</strong> {action}
</div>
<div style="font-size: 0.885rem; color: #EFE4F5; line-height: 1.5;">
<strong style="color: #F59E51;">🛠️ Hands-on Project:</strong> {project}
</div>
</div>
""").strip()
        st.markdown(card_html, unsafe_allow_html=True)
