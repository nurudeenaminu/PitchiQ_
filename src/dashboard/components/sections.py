"""Full UI sections composing multiple cards and logic."""
import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.components.theme import THEME
from src.dashboard.components.cards import render_match_row, render_kpi_row, render_ticker_card


def render_live_ticker_section(df: pd.DataFrame) -> None:
    """Render the live scores ticker section."""
    if df.empty:
        st.markdown('<div class="ticker">No live data available</div>', unsafe_allow_html=True)
        return

    st.subheader("Live Scores")
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.iterrows()):
        if i >= 3:
            break
        with cols[i]:
            render_ticker_card(
                row["league"], 
                row["home_team"], 
                row["away_team"], 
                int(row["home_goals"]), 
                int(row["away_goals"])
            )


def render_upcoming_fixtures_section(fixtures: pd.DataFrame, league: str, on_predict_callback=None) -> None:
    """Render upcoming fixtures list with predict CTAs."""
    st.subheader(f"Upcoming Fixtures: {league}")
    
    if fixtures.empty:
        st.info("No upcoming fixtures available")
        return

    for _, match in fixtures.iterrows():
        render_match_row(match, league, on_predict_callback)


def render_league_table_section(league_df: pd.DataFrame) -> None:
    """Render full league standings table."""
    if league_df.empty:
        st.info("No league table data available")
        return

    from src.dashboard.services.data import build_league_table
    table = build_league_table(league_df)
    
    if table.empty:
        st.info("No table data")
    else:
        st.dataframe(table, width='stretch')


def render_xg_snapshot_section(league_df: pd.DataFrame, league_teams: list[str]) -> None:
    """Render xG for/against scatter plot."""
    if league_df.empty:
        st.info("No xG data available")
        return

    from src.dashboard.services.data import get_team_xg_snapshot
    xg_df = get_team_xg_snapshot(league_df, league_teams)

    if xg_df.empty:
        st.info("No team xG data")
    else:
        fig = px.scatter(
            xg_df, 
            x="Avg xG For", 
            y="Avg xG Against", 
            text="Team", 
            height=420, 
            title="xG For vs Against"
        )
        fig.update_layout(paper_bgcolor=THEME["bg"], plot_bgcolor=THEME["bg"])
        st.plotly_chart(fig, width='stretch')


def render_prediction_output(pred: dict) -> None:
    """Render prediction results: probabilities, confidence, and chart."""
    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("Home Win", f"{pred.get('home_win', 0.0):.1%}")
    with p2:
        st.metric("Draw", f"{pred.get('draw', 0.0):.1%}")
    with p3:
        st.metric("Away Win", f"{pred.get('away_win', 0.0):.1%}")

    st.info(f"Confidence: {pred.get('confidence', 'n/a')}")

    chart = pd.DataFrame({
        "Outcome": ["Home", "Draw", "Away"],
        "Probability": [
            pred.get("home_win", 0.0),
            pred.get("draw", 0.0),
            pred.get("away_win", 0.0),
        ],
    })
    fig = px.bar(chart, x="Outcome", y="Probability", color="Outcome", title="Prediction Output")
    fig.update_layout(paper_bgcolor=THEME["bg"], plot_bgcolor=THEME["bg"])
    st.plotly_chart(fig, width='stretch')
