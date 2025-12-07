import matplotlib.pyplot as plt
import streamlit as st 
from tree_plots import assign_colors
from typing import Dict, List
import pandas as pd

from config import (
    DIAMETER_COL, SPECIES_COL, MATPLOTLIB_FIGSIZE_SQUARE,
    MATPLOTLIB_FIGSIZE_WIDE
)

@st.cache_data
def diversity_plot(species_counts: pd.Series, colourwheel: Dict) -> None:
    """Create pie chart of species diversity.
    
    Parameters
    ----------
    species_counts : pd.Series
        Count of trees per species
    colourwheel : dict
        Mapping of species to colors
    """
    fig, ax = plt.subplots(figsize=MATPLOTLIB_FIGSIZE_SQUARE)
    species_counts.plot(kind="pie", ax=ax, color=colourwheel)
    ax.set_title("Tree Species Diversity")
    ax.set_xlabel("Species")
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig)

def dbh_plot(df: pd.DataFrame, selected_species: List[str], numbins: int, 
             colourwheel: Dict, colourtype: bool) -> None:
    """Create histogram of DBH distribution by species.
    
    Parameters
    ----------
    df : pd.DataFrame
        Tree data with Species and DBH columns
    selected_species : list
        Species to include in plot
    numbins : int or array
        Bin edges or number of bins
    colourwheel : dict
        Mapping of species to colors
    colourtype : bool
        Whether to use species-specific colors
    """
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
    
    
