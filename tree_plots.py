import matplotlib.pyplot as plt
import streamlit as st 
from collections import defaultdict
import itertools
import pandas as pd
from typing import Optional, Dict, Any

from config import (
    DIAMETER_COL, SPECIES_COL, STATUS_COL, CROWN_COL,
    KNOWN_SPECIES_COLORS, PLOT_SIZE_METERS, PLOT_CENTER, DBH_MARKER_SCALE,
    LEGEND_DBH_SIZES, MATPLOTLIB_FIGSIZE_SQUARE, DEFAULT_GRID_STYLE, DEFAULT_GRID_WIDTH,
    DATE_COL, YEAR_COL
)

@st.cache_data
def load_data(filelike) -> Optional[pd.DataFrame]:
    """Load and prepare CSV data for tree plot analysis.
    
    Parameters
    ----------
    filelike : file-like object
        CSV file uploaded via Streamlit
        
    Returns
    -------
    pd.DataFrame or None
        Cleaned DataFrame with standardized column names and parsed dates,
        or None if loading fails
    """
    if filelike is not None:
        try:
            df = pd.read_csv(filelike)
            df.columns = df.columns.str.strip()

            if DATE_COL in df.columns:
                df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors='coerce', dayfirst=False)
                df[YEAR_COL] = df[DATE_COL].dt.year
            else:
                st.warning("No 'Date' column found. Year-based filtering will not be available.")

            st.success("File successfully uploaded and read.")
            return df
        except (pd.errors.ParserError, ValueError) as e:
            st.error(f"Error reading file: {e}")
            return None
    return None


def assign_colors(species_list) -> Dict[Any, str]:
    """Assign consistent colors to species for plotting.
    
    Parameters
    ----------
    species_list : iterable
        List of species identifiers
        
    Returns
    -------
    defaultdict
        Mapping of species to color, with fallback to matplotlib color cycle
    """
    color_cycle = itertools.cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])
    used = set(KNOWN_SPECIES_COLORS.values())
    color_cycle = (c for c in color_cycle if c not in used)

    mapping = dict(KNOWN_SPECIES_COLORS)
    
    try:
        species_iter = [s for s in set(species_list) if pd.notnull(s)]
    except (TypeError, AttributeError):
        species_iter = []

    for sp in sorted(species_iter):
        if sp not in mapping:
            mapping[sp] = next(color_cycle)

    return defaultdict(lambda: next(color_cycle), mapping)

def plot_data(df: pd.DataFrame, species_colors: Dict, plotting_group: str, year: int) -> str:
    """Create matplotlib scatter plot of trees colored by specified attribute.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing tree data with X, Y, DBH columns
    species_colors : dict
        Mapping of species/attribute values to colors
    plotting_group : str
        Column name to color by (e.g., 'Species', 'Status')
    year : int
        Year to filter data by
        
    Returns
    -------
    str
        Filename of saved plot image
    """
    if YEAR_COL not in df.columns:
        raise ValueError(f"DataFrame must contain '{YEAR_COL}' column")
    if plotting_group not in df.columns:
        raise ValueError(f"DataFrame must contain '{plotting_group}' column")
    
    fig, ax = plt.subplots(figsize=MATPLOTLIB_FIGSIZE_SQUARE)
    df_year = df[df[YEAR_COL] == year]
    
    if df_year.empty:
        raise ValueError(f"No data found for year {year}")
    
    for sp, group in df_year.groupby(plotting_group):
        ax.scatter(group["X"], group["Y"], s=group[DIAMETER_COL] * DBH_MARKER_SCALE, 
                   c=species_colors[sp], label=sp, marker='o', alpha=0.8)
    
    ax.legend()
    ax.grid(True, which='both', linestyle=DEFAULT_GRID_STYLE, linewidth=DEFAULT_GRID_WIDTH)
    ax.axvline(x=PLOT_CENTER, color='red', linestyle='-', linewidth=1)
    ax.axhline(y=PLOT_CENTER, color='red', linestyle='-', linewidth=1)
    ax.set_xlim(0, PLOT_SIZE_METERS)
    ax.set_ylim(0, PLOT_SIZE_METERS)
    ax.set_xticks(range(0, PLOT_SIZE_METERS + 1, 1))
    ax.set_yticks(range(0, PLOT_SIZE_METERS + 1, 1))
    ax.set_xlabel('Meters (x)')
    ax.set_ylabel('Meters (y)')
    ax.set_title(f'Tree Plot by {plotting_group}, {year}, Scaled by DBH')

    marker_sizes = [dbh * DBH_MARKER_SCALE for dbh in LEGEND_DBH_SIZES]
    [plt.scatter([], [], s=size, color='gray', label=f"{dbh} cm", alpha=0.6)
     for dbh, size in zip(LEGEND_DBH_SIZES, marker_sizes)]

    ax.legend(title=plotting_group, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)
    fn = 'tree_plot.png'
    plt.savefig(fn)
    return fn



