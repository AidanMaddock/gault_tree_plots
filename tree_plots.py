import matplotlib.pyplot as plt
import streamlit as st 
from collections import defaultdict
import itertools
import pandas as pd
from typing import Optional, Dict, Any
from matplotlib.lines import Line2D
import numpy as np

from config import (
    DIAMETER_COL, SPECIES_COL, STATUS_COL, CROWN_COL,
    KNOWN_SPECIES_COLORS, PLOT_SIZE_METERS, PLOT_CENTER, DBH_MARKER_SCALE,
    LEGEND_DBH_SIZES, MATPLOTLIB_FIGSIZE_SQUARE, DEFAULT_GRID_STYLE, DEFAULT_GRID_WIDTH,
    DATE_COL, YEAR_COL, COORD_X_ALIASES, COORD_Y_ALIASES
)

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
                df[YEAR_COL] = pd.to_numeric(df["YearInv"].astype(str).str.strip(), errors='coerce').astype('Int64')
            elif YEAR_COL in df.columns:
                # handle the case where CSV already has a Year column with stray whitespace or string types
                df[YEAR_COL] = pd.to_numeric(df[YEAR_COL].astype(str).str.strip(), errors='coerce').astype('Int64')
            else:
                st.warning("No date/year column found. Year-based filtering will not be available.")

            # Handle Plot/Subplot columns
            if ("Plots" in df.columns and "Subplots" in df.columns) or ("Plot" in df.columns and "SubPlot" in df.columns):
                plots_col = "Plots" if "Plots" in df.columns else "Plot"
                subplots_col = "Subplots" if "Subplots" in df.columns else "SubPlot"
                df["PlotID"] = df[plots_col].astype(str) + "-" + df[subplots_col].astype(str)
                df["PlotDisplay"] = df[plots_col].astype(str) + " - " + df[subplots_col].astype(str)
            elif "Plot" in df.columns and "PlotID" not in df.columns:
                # If only Plot column exists (no SubPlot), use it as PlotID but keep as numeric
                df["PlotID"] = pd.to_numeric(df["Plot"], errors='coerce').fillna(df["Plot"])
            elif "Plots" in df.columns and "PlotID" not in df.columns:
                # If only Plots column exists (no Subplots), use it as PlotID but keep as numeric
                df["PlotID"] = pd.to_numeric(df["Plots"], errors='coerce').fillna(df["Plots"])

            st.success("File successfully uploaded and read.")
            return df
        except (pd.errors.ParserError, ValueError) as e:
            st.error(f"Error reading file: {e}")
            return None
    return None


def normalize_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Rename coordinate columns to 'X' and 'Y' if needed."""
    df = df.copy()

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
    for alias in COORD_X_ALIASES:
        if alias in df.columns and 'X' not in df.columns:
            df.rename(columns={alias: 'X'}, inplace=True)
            break
    for alias in COORD_Y_ALIASES:
        if alias in df.columns and 'Y' not in df.columns:
            df.rename(columns={alias: 'Y'}, inplace=True)
            break

    # Only apply string normalization to PlotDisplay column (not PlotID which should remain numeric)
    for col in df.columns:
        if col == "PlotDisplay":  # Only process PlotDisplay, not PlotID
            df[col] = df[col].astype(str).str.replace('\u00A0', ' ')  # NBSP -> space
            df[col] = df[col].str.strip()
            df[col] = df[col].str.replace(r'\s*-\s*', '-', regex=True)
    
    return df


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
    
    try:
        year_int = int(year)
    except Exception:
        year_int = year

    # Coerce numeric columns used for plotting
    # creates copies of numeric versions to keep original df untouched
    df = df.copy()
    df["X"] = pd.to_numeric(df["X"], errors='coerce')
    df["Y"] = pd.to_numeric(df["Y"], errors='coerce')
    df[DIAMETER_COL] = pd.to_numeric(df[DIAMETER_COL], errors='coerce')

    fig, ax = plt.subplots(figsize=MATPLOTLIB_FIGSIZE_SQUARE)
    df_year = df[df[YEAR_COL] == year_int]

    if df_year.empty:
        st.warning(f"No data found for year {year} after coercion (year value used: {year_int}). "
                   "Check YEAR_COL types and values in your DataFrame.")
        raise ValueError(f"No data found for year {year}")

    # Require numeric/finite X,Y,DBH and a valid plotting_group
    df_year = df_year.dropna(subset=["X", "Y", DIAMETER_COL, plotting_group])
    # also enforce finite numeric values (excludes inf/-inf)
    df_year = df_year[np.isfinite(df_year["X"]) & np.isfinite(df_year["Y"]) & np.isfinite(df_year[DIAMETER_COL])]

    if df_year.empty:
        st.warning(f"No data found for year {year} with numeric X, Y, and {DIAMETER_COL} after coercion.")
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



