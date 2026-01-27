import pandas as pd
import numpy as np
import math
from typing import Optional, Tuple

from config import DIAMETER_COL, SPECIES_COL, MIN_SAMPLES_FOR_STATS, TREEID_COL, PLOTID_COL

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


def compute_plot_year_stats(df: pd.DataFrame, plot_id: str) -> Optional[dict]:
    """Compute aggregated statistics by year for a plot.
    
    Parameters
    ----------
    df : pd.DataFrame
        Tree data with Year, PlotID, Species, and DBH columns
    plot_id : str
        Plot identifier to filter by, or None if df is already filtered
        
    Returns
    -------
    dict or None
        Dictionary with 'counts_df', 'basal_area_df', 'species_df' DataFrames,
        or None if plot has no data or insufficient time-series data
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


def t_statistic_independent(a: np.ndarray, b: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
    """Compute Welch t-statistic for independent samples.
    
    Parameters
    ----------
    a, b : np.ndarray
        Two samples to compare
        
    Returns
    -------
    tuple
        (t-statistic, degrees of freedom) or (None, None) if invalid
    """
    if a is None or b is None or len(a) < MIN_SAMPLES_FOR_STATS or len(b) < MIN_SAMPLES_FOR_STATS:
        return None, None
    
    n1 = len(a)
    n2 = len(b)
    m1 = float(np.nanmean(a))
    m2 = float(np.nanmean(b))
    s1 = float(np.nanvar(a, ddof=1))
    s2 = float(np.nanvar(b, ddof=1))
    denom = math.sqrt(s1 / n1 + s2 / n2)
    
    if denom == 0:
        return None, None
    
    t = (m1 - m2) / denom
    num = (s1 / n1 + s2 / n2) ** 2
    den = (s1 ** 2) / (n1 ** 2 * (n1 - 1)) + (s2 ** 2) / (n2 ** 2 * (n2 - 1))
    
    df = num / den if den != 0 else None
    return t, df


def diversity(data: Optional[pd.DataFrame]) -> int:
    """Count unique species in dataset.
    
    Parameters
    ----------
    data : pd.DataFrame or None
        Tree data with Species column
        
    Returns
    -------
    int
        Number of unique species
    """
    if data is None or data.empty:
        return 0
    return len(data[SPECIES_COL].unique())