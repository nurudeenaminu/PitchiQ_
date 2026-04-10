"""Reusable card and metric components for PitchIQ dashboard."""
import streamlit as st
import pandas as pd
from src.dashboard.components.theme import THEME


def _kpi_icon(label: str) -> str:
    """Map KPI labels to Font Awesome icons."""
    icon_map = {
        "total teams": "fa-users",
        "matches played": "fa-calendar-check",
        "goals scored": "fa-futbol",
        "avg goals/game": "fa-chart-line",
        "log loss": "fa-scale-balanced",
        "macro f1": "fa-bullseye",
        "roc auc": "fa-wave-square",
        "accuracy": "fa-crosshairs",
    }
    return icon_map.get(label.strip().lower(), "fa-circle-nodes")


def render_kpi_card(label: str, value: str, color: str = None) -> None:
    """Render a single KPI metric card."""
    color = color or THEME["accent"]
    icon = _kpi_icon(label)
    st.markdown(
        (
            f'<div class="card">'
            f'<div class="kpi-label"><i class="fa-solid {icon}"></i>{label}</div>'
            f'<h3 class="kpi-value" style="color:{color}">{value}</h3>'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )


def render_kpi_row(metrics: list[dict]) -> None:
    """Render 4-column KPI row. Each dict must have 'label', 'value', optional 'color'."""
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            render_kpi_card(metric["label"], metric["value"], metric.get("color"))


def render_hero_banner(title: str, subtitle: str) -> None:
    """Render the hero banner at page top."""
    st.markdown(
        (
            '<div class="hero">'
            f'<div class="hero-title">{title}</div>'
            f'<div class="hero-sub">{subtitle}</div>'
            '<div class="hero-badges">'
            '<span class="hero-badge"><i class="fa-solid fa-satellite-dish"></i>Live Signals</span>'
            '<span class="hero-badge"><i class="fa-solid fa-shield-halved"></i>Model Verified</span>'
            '<span class="hero-badge"><i class="fa-solid fa-bolt"></i>Fast Inference</span>'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_ticker_card(league: str, home: str, away: str, home_goals: int, away_goals: int) -> None:
    """Render a single live score ticker card."""
    st.markdown(
        (
            '<div class="ticker">'
            '<i class="fa-solid fa-signal" style="margin-right:8px;color:#3ddc97"></i>'
            f'{league} · {home} <strong>{home_goals}-{away_goals}</strong> {away}'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_match_row(match: pd.Series, league: str, on_predict_callback=None) -> None:
    """Render a fixture row with predict button. Calls callback if provided."""
    c1, c2, c3, c4 = st.columns([2.2, 0.8, 2.2, 1.5])
    with c1:
        st.markdown(f"<div class='match-row'><strong><i class='fa-solid fa-house'></i> {match['home_team']}</strong></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='text-align:center;padding-top:7px;color:#86a7be;font-weight:700'>VS</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='match-row'><strong><i class='fa-solid fa-plane-departure'></i> {match['away_team']}</strong></div>", unsafe_allow_html=True)
    with c4:
        if st.button("Forecast", key=f"predict_{league}_{match['home_team']}_{match['away_team']}"):
            if on_predict_callback:
                on_predict_callback(match)


def render_error_box(message: str) -> None:
    """Render an error message box."""
    st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)


def render_success_box(message: str) -> None:
    """Render a success message box."""
    st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
