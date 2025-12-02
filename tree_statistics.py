import pandas as pd
import numpy as np
import math


def basal_area_m2(dbh_cm: float) -> float:
    """Return basal area in square meters given DBH in centimeters.

    Basal area (m^2) = pi * (dbh_m / 2) ** 2, where dbh_m = dbh_cm / 100
    """
    if dbh_cm is None or pd.isna(dbh_cm):
        return 0.0
    dbh_m = dbh_cm / 100.0
    r = dbh_m / 2.0
    return math.pi * (r ** 2)


def compute_plot_year_stats(df: pd.DataFrame, plot_id: str):
    """Return aggregated statistics per year for a particular plot.

    Returns a dict with three DataFrames:
      - counts_df: columns ['Year', 'PlotID', 'Count']
      - basal_area_df: columns ['Year', 'PlotID', 'BasalArea_m2']
      - species_df: columns ['Year', 'PlotID', 'Species', 'Count', 'Proportion']
    """
    if df is None:
        return None
    # Filter for the plot
    plot_df = df[df['PlotID'] == plot_id].copy()
    if plot_df.empty:
        return None

    # Ensure Year exists
    if 'Year' not in plot_df.columns:
        # Try to infer from Date
        if 'Date' in plot_df.columns:
            plot_df['Year'] = pd.to_datetime(plot_df['Date'], errors='coerce').dt.year
        else:
            raise ValueError('DataFrame must contain Year or Date for time-based statistics')

    # Tree counts per year
    counts = plot_df.groupby('Year').size().reset_index(name='Count')
    counts['PlotID'] = plot_id

    # Basal area per year
    plot_df['BasalArea'] = plot_df['DBH'].apply(basal_area_m2)
    basal_area = plot_df.groupby('Year')['BasalArea'].sum().reset_index()
    basal_area['PlotID'] = plot_id
    basal_area = basal_area.rename(columns={'BasalArea': 'BasalArea_m2'})

    # Species composition per year
    species = (
        plot_df.groupby(['Year', 'Species']).size().reset_index(name='Count')
    )
    # Convert to proportions
    yearly_total = species.groupby('Year')['Count'].transform('sum')
    species['Proportion'] = species['Count'] / yearly_total
    species['PlotID'] = plot_id

    return {
        'counts_df': counts,
        'basal_area_df': basal_area,
        'species_df': species,
    }


def compute_dbh_increments(df: pd.DataFrame, plot_id: str):
    """Compute per-interval DBH increments (cm/year) for a given plot.

    Returns a numpy array of increments (one per interval per tree).
    """
    if df is None:
        return None
    plot_df = df[df['PlotID'] == plot_id].copy()
    if plot_df.empty:
        return None

    # Ensure Year exists
    if 'Year' not in plot_df.columns:
        if 'Date' in plot_df.columns:
            plot_df['Year'] = pd.to_datetime(plot_df['Date'], errors='coerce').dt.year
        else:
            raise ValueError('DataFrame must contain Year or Date for increment computation')

    increments = []
    for tree_id, group in plot_df.groupby('TreeID'):
        g = group.sort_values('Year')
        # compute increments between successive years
        years = g['Year'].values
        dbhs = g['DBH'].values
        if len(years) < 2:
            continue
        # compute the pairwise deltas
        for i in range(len(years) - 1):
            dy = years[i+1] - years[i]
            if dy <= 0:
                continue
            delta_dbh = dbhs[i+1] - dbhs[i]
            increments.append(delta_dbh / dy)

    if len(increments) == 0:
        return None
    return np.array(increments)


def t_statistic_independent(a: np.ndarray, b: np.ndarray):
    """Compute Welch t-statistic for two independent samples.

    Returns (t_stat, df)
    """
    if a is None or b is None or len(a) < 2 or len(b) < 2:
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
    # Welch–Satterthwaite df approximation
    num = (s1 / n1 + s2 / n2) ** 2
    den = (s1 ** 2) / (n1 ** 2 * (n1 - 1)) + (s2 ** 2) / (n2 ** 2 * (n2 - 1))
    if den == 0:
        df = None
    else:
        df = num / den
    return t, df


def diversity(data):
    # simple diversity stub: return number of unique species
    if data is None:
        return 0
    return len(data['Species'].unique())