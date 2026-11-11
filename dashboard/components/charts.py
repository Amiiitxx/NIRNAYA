"""
Module: dashboard.components.charts
Description: Reusable Plotly chart generators customized for NIRNAYA purple and orange palette:
Deep Purple (#3A0353), Card Surface (#4B0968), Orange (#F59E51), Light Orange (#F8D299), Primary Purple (#804A8A).
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional, Union

# NIRNAYA Core Palette
DEEP_PURPLE = "#3A0353"
CARD_PURPLE = "#4B0968"
PRIMARY_PURPLE = "#804A8A"
ORANGE_PRIMARY = "#F59E51"
LIGHT_ORANGE = "#F8D299"
BORDER_PURPLE = "#681989"

THEME_PALETTE = [
    "#F59E51",  # Orange
    "#804A8A",  # Primary Purple
    "#F8D299",  # Light Orange
    "#A85CB5",  # Bright Purple
    "#FB923C",  # Tangerine
    "#C084FC",  # Soft Violet
    "#FBBF24",  # Amber
    "#34D399",  # Emerald
    "#38BDF8",  # Sky Blue
    "#F43F5E",  # Rose Red
]


def apply_dark_layout(
    fig: go.Figure,
    title: str = "",
    height: int = 380,
    show_legend: bool = False,
) -> go.Figure:
    """
    Applies consistent NIRNAYA deep purple and orange styling to any Plotly figure.
    """
    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 15, "color": "#FFFFFF", "family": "Plus Jakarta Sans, Inter, sans-serif"},
            "x": 0.02,
            "y": 0.95,
        },
        paper_bgcolor=DEEP_PURPLE,
        plot_bgcolor=CARD_PURPLE,
        height=height,
        margin={"l": 40, "r": 30, "t": 50, "b": 40},
        font={"color": LIGHT_ORANGE, "family": "Plus Jakarta Sans, Inter, sans-serif", "size": 12},
        showlegend=show_legend,
        legend={
            "font": {"color": "#FFFFFF"},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )
    fig.update_xaxes(
        gridcolor=BORDER_PURPLE,
        zerolinecolor=BORDER_PURPLE,
        tickfont={"color": "#EFE4F5"},
        title_font={"color": LIGHT_ORANGE},
    )
    fig.update_yaxes(
        gridcolor=BORDER_PURPLE,
        zerolinecolor=BORDER_PURPLE,
        tickfont={"color": "#EFE4F5"},
        title_font={"color": LIGHT_ORANGE},
    )
    return fig


def create_bar_chart(
    data: Union[pd.DataFrame, Dict[str, Union[int, float]]],
    x: str,
    y: str,
    title: str,
    horizontal: bool = False,
    color_col: Optional[str] = None,
    height: int = 380,
    text_auto: bool = True,
) -> go.Figure:
    """
    Creates a responsive vertical or horizontal bar chart with NIRNAYA colors.
    """
    if isinstance(data, dict):
        df = pd.DataFrame(list(data.items()), columns=[x, y])
    else:
        df = data.copy()

    if horizontal:
        fig = px.bar(
            df,
            x=x,
            y=y,
            orientation="h",
            color=color_col or x,
            color_discrete_sequence=THEME_PALETTE,
            text_auto=text_auto,
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig = px.bar(
            df,
            x=x,
            y=y,
            color=color_col or x,
            color_discrete_sequence=THEME_PALETTE,
            text_auto=text_auto,
        )

    return apply_dark_layout(fig, title=title, height=height)


def create_donut_chart(
    data: Union[pd.DataFrame, Dict[str, Union[int, float]]],
    names: str,
    values: str,
    title: str,
    height: int = 360,
    hole: float = 0.55,
) -> go.Figure:
    """
    Creates a modern donut chart for categorical distributions.
    """
    if isinstance(data, dict):
        df = pd.DataFrame(list(data.items()), columns=[names, values])
    else:
        df = data.copy()

    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=hole,
        color_discrete_sequence=THEME_PALETTE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        marker=dict(line=dict(color=DEEP_PURPLE, width=2)),
    )
    return apply_dark_layout(fig, title=title, height=height, show_legend=True)


def create_histogram(
    series: Union[pd.Series, List[float]],
    title: str,
    x_title: str = "Salary (LPA)",
    nbins: int = 35,
    height: int = 380,
) -> go.Figure:
    """
    Creates a continuous distribution histogram using NIRNAYA orange.
    """
    fig = px.histogram(
        x=series,
        nbins=nbins,
        color_discrete_sequence=[ORANGE_PRIMARY],
        opacity=0.88,
    )
    fig.update_layout(xaxis_title=x_title, yaxis_title="Job Count")
    return apply_dark_layout(fig, title=title, height=height)


def create_box_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    height: int = 420,
) -> go.Figure:
    """
    Creates a multi-group box plot comparing continuous targets.
    """
    fig = px.box(
        df,
        x=x,
        y=y,
        color=x,
        color_discrete_sequence=THEME_PALETTE,
    )
    return apply_dark_layout(fig, title=title, height=height, show_legend=False)


def create_gauge_chart(
    score: float,
    title: str = "Skill Match Score",
    max_score: float = 100.0,
    height: int = 280,
) -> go.Figure:
    """
    Creates a circular gauge chart for candidate skill match percentage.
    """
    score_clamped = min(max_score, max(0.0, float(score)))

    # Determine bar color based on score tier
    if score_clamped >= 75.0:
        bar_color = "#10B981"  # Emerald
    elif score_clamped >= 50.0:
        bar_color = ORANGE_PRIMARY
    else:
        bar_color = "#F43F5E"  # Rose

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_clamped,
            number={"suffix": "%", "font": {"size": 38, "color": "#FFFFFF"}},
            title={"text": title, "font": {"size": 14, "color": LIGHT_ORANGE}},
            gauge={
                "axis": {"range": [0, max_score], "tickwidth": 1, "tickcolor": LIGHT_ORANGE},
                "bar": {"color": bar_color, "thickness": 0.28},
                "bgcolor": CARD_PURPLE,
                "borderwidth": 1,
                "bordercolor": BORDER_PURPLE,
                "steps": [
                    {"range": [0, 49.9], "color": "rgba(244, 63, 94, 0.2)"},
                    {"range": [50.0, 74.9], "color": "rgba(245, 158, 81, 0.25)"},
                    {"range": [75.0, 100.0], "color": "rgba(16, 185, 129, 0.25)"},
                ],
            },
        )
    )
    return apply_dark_layout(fig, title="", height=height)
