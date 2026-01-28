import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import streamlit as st 
from typing import Optional, Tuple, Dict, List
from tree_plots import assign_colors

from config import (
    DIAMETER_COL, SPECIES_COL, MIN_SAMPLES_FOR_STATS, TREEID_COL, PLOTID_COL, MATPLOTLIB_FIGSIZE_SQUARE,
    MATPLOTLIB_FIGSIZE_WIDE
)

def basal_area_m2(dbh_cm: float) -> float:
    """Calculate basal area in square meters from DBH.
    
    Parameters
    ----------
    dbh_cm : float
        Diameter at breast height in centimeters
        
    Returns
    -------
    float
        Basal area in square meters
    """
    if dbh_cm is None or pd.isna(dbh_cm):
        return 0.0
    dbh_m = dbh_cm / 100.0
    r = dbh_m / 2.0
    return math.pi * (r ** 2)

    """Compute aggregated statistics by year for a plot."""
def compute_plot_year_stats(df: pd.DataFrame, plot_id: str) -> Optional[dict]:

    if df is None:
        return None
    
    if plot_id is not None and PLOTID_COL in df.columns:
        plot_df = df[df[PLOTID_COL] == plot_id].copy()
    else:
        plot_df = df.copy()
    
    if plot_df.empty:
        return None

    if 'Year' not in plot_df.columns:
        if 'Date' in plot_df.columns:
            plot_df['Year'] = pd.to_datetime(plot_df['Date'], errors='coerce').dt.year
        elif 'YearInv' in plot_df.columns:
            plot_df['Year'] = plot_df['YearInv']
        else:
            raise ValueError('DataFrame must contain Year, Date, or YearInv for time-based statistics')

    counts = plot_df.groupby('Year').size().reset_index(name='Count')
    counts['PlotID'] = plot_id if plot_id is not None else 'Plot'

    plot_df['BasalArea'] = plot_df[DIAMETER_COL].apply(basal_area_m2)
    basal_area = plot_df.groupby('Year')['BasalArea'].sum().reset_index()
    basal_area['PlotID'] = plot_id if plot_id is not None else 'Plot'
    basal_area = basal_area.rename(columns={'BasalArea': 'BasalArea_m2'})

    species = (
        plot_df.groupby(['Year', SPECIES_COL]).size().reset_index(name='Count')
    )
    yearly_total = species.groupby('Year')['Count'].transform('sum')
    species['Proportion'] = species['Count'] / yearly_total
    species['PlotID'] = plot_id if plot_id is not None else 'Plot'

    return {
        'counts_df': counts,
        'basal_area_df': basal_area,
        'species_df': species,
    }


def compute_dbh_increments(df: pd.DataFrame, plot_id: str) -> Optional[np.ndarray]:
    """Compute annual DBH increments for trees in a plot.
    
    Parameters
    ----------
    df : pd.DataFrame
        Tree data with PlotID, StandardID, Year, and DBH columns
    plot_id : str
        Plot identifier to filter by, or None if df is already filtered
        
    Returns
    -------
    np.ndarray or None
        Array of annual increment values (cm/year), or None if insufficient data
    """
    if df is None:
        return None
    
    if plot_id is not None and PLOTID_COL in df.columns:
        plot_df = df[df[PLOTID_COL] == plot_id].copy()
    else:
        plot_df = df.copy()
    
    if plot_df.empty:
        return None

    if 'Year' not in plot_df.columns:
        if 'Date' in plot_df.columns:
            plot_df['Year'] = pd.to_datetime(plot_df['Date'], errors='coerce').dt.year
        elif 'YearInv' in plot_df.columns:
            plot_df['Year'] = plot_df['YearInv']
        else:
            raise ValueError('DataFrame must contain Year, Date, or YearInv for increment computation')

    increments = []
    for tree_id, group in plot_df.groupby(TREEID_COL):
        g = group.sort_values('Year')
        years = g['Year'].values
        dbhs = g[DIAMETER_COL].values
        
        if len(years) < 2:
            continue
        
        for i in range(len(years) - 1):
            dy = years[i+1] - years[i]
            if dy <= 0:
                continue
            delta_dbh = dbhs[i+1] - dbhs[i]
            increments.append(delta_dbh / dy)

    return np.array(increments) if len(increments) > 0 else None

"""Count unique species in dataset."""
def diversity(data: Optional[pd.DataFrame]) -> int:

    if data is None or data.empty:
        return 0
    return len(data[SPECIES_COL].unique())

"""Create pie chart of species diversity."""
@st.cache_data
def diversity_plot(species_counts: pd.Series, colourwheel: Dict) -> None:
    fig, ax = plt.subplots(figsize=MATPLOTLIB_FIGSIZE_SQUARE)
    species_counts.plot(kind="pie", ax=ax, color=colourwheel)
    ax.set_title("Tree Species Diversity")
    ax.set_xlabel("Species")
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig)

    """Create histogram of DBH distribution by species."""
def dbh_plot(df: pd.DataFrame, selected_species: List[str], numbins: int, 
             colourwheel: Dict, colourtype: bool) -> None:
    colors = plt.cm.tab20.colors
    color_map = {sp: colors[i % len(colors)] for i, sp in enumerate(selected_species)}
    fig, ax = plt.subplots(figsize=MATPLOTLIB_FIGSIZE_WIDE)
    
    for sp in selected_species:
        subset = df[df[SPECIES_COL] == sp][DIAMETER_COL].dropna()
        if len(subset) == 0:
            continue
        
        if colourtype:
            ax.hist(subset, bins=numbins, alpha=0.6, label=sp, color=colourwheel[sp])
            ax.legend(title="Species")
        else:
            ax.hist(subset, bins=numbins, alpha=0.6, label=sp, color="black")

    ax.set_title("DBH Distribution by Species")
    ax.set_xlabel(f"{DIAMETER_COL} (cm)")
    ax.set_ylabel("Number of Trees")
    st.pyplot(fig)
    
    