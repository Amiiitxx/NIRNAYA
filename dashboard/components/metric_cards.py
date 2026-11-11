"""
Module: dashboard.components.metric_cards
Description: Styled KPI cards with NIRNAYA purple and orange palette.
Guarantees clean HTML rendering by eliminating CommonMark markdown indentation blocks.
"""

import streamlit as st
import textwrap
from typing import List, Dict, Any, Optional

DEFAULT_ACCENT = "#F59E51"  # NIRNAYA Orange


def render_metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    tag: Optional[str] = None,
    border_accent: Optional[str] = None,
) -> None:
    """
    Renders an individual KPI card with NIRNAYA deep purple card background and orange accent.
    Guarantees zero leading indentation so CommonMark never wraps HTML in <pre><code>.
    """
    accent = border_accent or DEFAULT_ACCENT
    border_style = f"border-top: 3.5px solid {accent};"
    tag_html = (
        f'<span style="font-size: 0.72rem; font-weight: 700; background: rgba(245, 158, 81, 0.2); '
        f'color: #F8D299; border: 1px solid rgba(245, 158, 81, 0.4); padding: 2px 7px; '
        f'border-radius: 9999px; float: right;">{tag}</span>'
        if tag else ""
    )

    # Clean zero-indent HTML string to prevent CommonMark code block parsing
    html_block = textwrap.dedent(f"""
<div class="metric-card" style="{border_style}">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
<div class="metric-title">{title}</div>
{tag_html}
</div>
<div class="metric-value">{value}</div>
<div class="metric-subtitle">{subtitle}</div>
</div>
""").strip()

    st.markdown(html_block, unsafe_allow_html=True)


def render_kpi_row(cards: List[Dict[str, Any]]) -> None:
    """
    Renders a row of metric cards across equal-width columns.

    Args:
        cards: List of dicts, each with keys: 'title', 'value', 'subtitle', optional 'tag', optional 'accent'.
    """
    if not cards:
        return

    num_cols = len(cards)
    cols = st.columns(num_cols)

    for i, card in enumerate(cards):
        with cols[i]:
            render_metric_card(
                title=card.get("title", ""),
                value=card.get("value", ""),
                subtitle=card.get("subtitle", ""),
                tag=card.get("tag"),
                border_accent=card.get("accent"),
            )
