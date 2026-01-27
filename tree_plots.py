import matplotlib.pyplot as plt
import streamlit as st 
from collections import defaultdict
import itertools
import pandas as pd
from typing import Optional, Dict, Any
from matplotlib.lines import Line2D

from config import (
    DIAMETER_COL, SPECIES_COL, STATUS_COL, CROWN_COL,
    KNOWN_SPECIES_COLORS, PLOT_SIZE_METERS, PLOT_CENTER, DBH_MARKER_SCALE,
    LEGEND_DBH_SIZES, MATPLOTLIB_FIGSIZE_SQUARE, DEFAULT_GRID_STYLE, DEFAULT_GRID_WIDTH,
    DATE_COL, YEAR_COL
)

@st.cache_data
def load_data(filelike) -> Optional[pd.DataFrame]:
    if filelike is not None:
        try:
            df = pd.read_csv(filelike)
            df.columns = df.columns.str.strip()
            if "TreeStatus" in df.columns and "Status" not in df.columns:
                df.rename(columns={"TreeStatus": "Status"}, inplace=True)
            if "TreeID" in df.columns and "StandardID" not in df.columns:
                df.rename(columns={"TreeID": "StandardID"}, inplace=True)

            if DATE_COL in df.columns:
                df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors='coerce', dayfirst=False)
                df[YEAR_COL] = df[DATE_COL].dt.year
            elif "YearInv" in df.columns:
                df[YEAR_COL] = pd.to_numeric(df["YearInv"], errors='coerce').astype('int64')
            else:
                st.warning("No date/year column found. Year-based filtering will not be available.")

            if ("Plots" in df.columns and "Subplots" in df.columns) or ("Plot" in df.columns and "SubPlot" in df.columns):
                plots_col = "Plots" if "Plots" in df.columns else "Plot"
                subplots_col = "Subplots" if "Subplots" in df.columns else "SubPlot"
                df["PlotID"] = df[plots_col].astype(str) + "-" + df[subplots_col].astype(str)
                df["PlotDisplay"] = df[plots_col].astype(str) + " - " + df[subplots_col].astype(str)

            st.success("File successfully uploaded and read.")
            return df
        except (pd.errors.ParserError, ValueError) as e:
            st.error(f"Error reading file: {e}")
            return None
    return None


def assign_colors(species_list) -> Dict[Any, str]:
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
    
    if YEAR_COL not in df.columns:
        raise ValueError(f"DataFrame must contain '{YEAR_COL}' column")
    if plotting_group not in df.columns:
        raise ValueError(f"DataFrame must contain '{plotting_group}' column")
    
    fig, ax = plt.subplots(figsize=MATPLOTLIB_FIGSIZE_SQUARE)
    df_year = df[df[YEAR_COL] == year]
    
    if df_year.empty:
        raise ValueError(f"No data found for year {year}")
    
    # Filter out rows with missing required columns for plotting
    df_year = df_year.dropna(subset=["X", "Y", DIAMETER_COL, plotting_group])
    
    if df_year.empty:
        raise ValueError(f"No data found for year {year} with complete X, Y, {DIAMETER_COL}, and {plotting_group} values")
    
    for sp, group in df_year.groupby(plotting_group, dropna=True):
        if not group.empty and len(group) > 0:
            # Ensure all values are numeric and not NaN
            valid_mask = group[DIAMETER_COL].notna() & group["X"].notna() & group["Y"].notna()
            if valid_mask.sum() > 0:
                group_valid = group[valid_mask]
                ax.scatter(group_valid["X"], group_valid["Y"], s=group_valid[DIAMETER_COL] * DBH_MARKER_SCALE, 
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
    dbh_legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                                  markersize=size**0.5, label=f"{dbh} cm", alpha=0.6)
                           for dbh, size in zip(LEGEND_DBH_SIZES, marker_sizes)]
    
    # Get existing legend handles handling empty case
    existing_handles, existing_labels = ax.get_legend_handles_labels()
    all_handles = existing_handles + dbh_legend_elements
    
    if len(all_handles) > 0:
        ax.legend(handles=all_handles, 
                  title=plotting_group, bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        # Fallback if no legend elements
        ax.legend(handles=dbh_legend_elements, 
                  title=plotting_group, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)
    fn = 'tree_plot.png'
    plt.savefig(fn)
    return fn



