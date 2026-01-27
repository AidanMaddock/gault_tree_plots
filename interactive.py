import plotly.express as px
import streamlit as st 
import plotly.graph_objects as go
from typing import List, Tuple, Dict, Any
import pandas as pd

from config import (
    DIAMETER_COL, SPECIES_COL, STATUS_COL, CROWN_COL,
    PLOT_SIZE_METERS, DBH_MARKER_SCALE,
    PLOTLY_WIDTH_WIDE, PLOTLY_HEIGHT_WIDE, COORD_X_ALIASES, COORD_Y_ALIASES, TREEID_COL
)

def _normalize_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Rename coordinate columns to 'X' and 'Y' if needed."""
    df = df.copy()
    for alias in COORD_X_ALIASES:
        if alias in df.columns and 'X' not in df.columns:
            df.rename(columns={alias: 'X'}, inplace=True)
            break
    for alias in COORD_Y_ALIASES:
        if alias in df.columns and 'Y' not in df.columns:
            df.rename(columns={alias: 'Y'}, inplace=True)
            break
    return df

def get_dbh_history(df: pd.DataFrame, tree_id: str) -> Tuple[List[float], List[int]]:
    """Retrieve DBH history for a specific tree identified by tree_id."""
    tree_data = df[df[TREEID_COL] == tree_id].sort_values("Year")
    return list(tree_data[DIAMETER_COL]), list(tree_data["Year"])

def prepare_plot_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Prepare tree data for plotting, including historical DBH data."""
    df = _normalize_coordinates(df)
    df[TREEID_COL] = df['X'].astype(str) + "_" + df['Y'].astype(str)

    df_year = df[df['Year'] == year]
    history = df.groupby(TREEID_COL).apply(
        lambda group: group.sort_values("Year")[["Year", DIAMETER_COL]].values.tolist()
    ).to_dict()
    
    df_year = df_year.copy()
    df_year["customdata"] = df_year[TREEID_COL].map(history)
    return df_year

def plot_with_hover_line(df_year: pd.DataFrame) -> None:
    fig = go.Figure()

    for _, row in df_year.iterrows():
        years_dbh = row["customdata"]
        if not years_dbh:
            continue
        years, dbhs = zip(*years_dbh)

        fig.add_trace(go.Scatter(
            x=[row["X"]],
            y=[row["Y"]],
            mode='markers',
            marker=dict(size=row[DIAMETER_COL] * DBH_MARKER_SCALE, color='blue', opacity=0.7),
            hovertemplate=
            f'<b>StandardID: {row[TREEID_COL]}</b><br>' +
            'X: %{x}, Y: %{y}<br>' +
            f'{DIAMETER_COL}: ' + '%{marker.size:.1f}<br><br>' +
            f'{DIAMETER_COL} over Years:<br>' +
            ''.join(f'{y}: {d:.1f} cm<br>' for y, d in zip(years, dbhs)) +
            '<extra></extra>'
        ))

    fig.update_layout(
        title="Hover over a tree to see its DBH history",
        xaxis=dict(range=[0, PLOT_SIZE_METERS], title="Meters (x)"),
        yaxis=dict(range=[0, PLOT_SIZE_METERS], title="Meters (y)"),
        width=PLOTLY_WIDTH_WIDE,
        height=PLOTLY_HEIGHT_WIDE
    )

    st.plotly_chart(fig)


def plot_interactive(df: pd.DataFrame, year: int) -> None:

    df = _normalize_coordinates(df)
    df_year = df[df['Year'] == year]
    
    if df_year.empty:
        st.warning(f"No data found for year {year}.")
        return

    df_year = df_year.copy()
    df_year['DBH_size'] = df_year[DIAMETER_COL]
    fig = px.scatter(
        df_year,
        x='X',
        y='Y',
        color=SPECIES_COL,
        size='DBH_size',
        hover_data=[SPECIES_COL, DIAMETER_COL, STATUS_COL, CROWN_COL, 'Date'],
        title=f"Interactive Tree Plot for {year}",
        labels={'X': 'Meters (x)', 'Y': 'Meters (y)'},
        width=PLOTLY_WIDTH_WIDE,
        height=PLOTLY_HEIGHT_WIDE
    )

    fig.update_traces(marker=dict(opacity=0.8), selector=dict(mode='markers'))
    fig.update_layout(yaxis_range=[0, PLOT_SIZE_METERS], xaxis_range=[0, PLOT_SIZE_METERS])
    st.plotly_chart(fig, use_container_width=True)
