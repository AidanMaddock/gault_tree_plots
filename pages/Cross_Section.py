import streamlit as st
st.set_page_config(page_title="Cross Section")
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tree_plots import load_data, plot_data, assign_colors
from interactive import plot_interactive
from statistics_1 import diversity_plot, dbh_plot
from typing import Optional
import pandas as pd 
import numpy as np

from config import (
    DIAMETER_COL, PLOT_SIZE_METERS, SPECIES_COL, STATUS_COL, CROWN_COL,
    WELCOME_TEXT, DEFAULT_BINS, MIN_BINS, MAX_BINS,
    DEFAULT_YEAR_TEXT_FORMAT, COORD_X_ALIASES, COORD_Y_ALIASES, PLOTID_COL
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

def dbh_app(df: pd.DataFrame, colors: dict) -> None:
    species_list = sorted(df[SPECIES_COL].dropna().unique())
    species_options = ["Select All"] + list(species_list)
    selected = st.multiselect("Choose species:", options=species_options, default=["Select All"])

    if "Select All" in selected:
        selected_species = list(species_list)
    else:
        selected_species = selected

    filtered_df = df[df[SPECIES_COL].isin(selected_species)]
    
    num_bins = st.slider("Number of bins for DBH histogram", min_value=MIN_BINS, max_value=MAX_BINS, value=DEFAULT_BINS)
    all_dbh = df[DIAMETER_COL].dropna()
    
    if len(all_dbh) == 0:
        st.warning("No DBH data available.")
        return
    
    bin_edges = np.histogram_bin_edges(all_dbh, bins=num_bins)
    one_colour = st.checkbox("Use Species-Specific Colouring", value=True)
    dbh_plot(filtered_df, selected_species, bin_edges, colors, one_colour)
    
    if selected_species:
        avg_dbh = filtered_df[DIAMETER_COL].mean()
        st.write(f"Average {DIAMETER_COL}: {avg_dbh:.2f} cm")


st.title("Tree Plot Visualizer")
st.write(WELCOME_TEXT)

with st.sidebar:
    file_option = st.radio("Data source:", ["Upload your data", "See an example"], horizontal=True)

    if file_option == "See an example":
        uploaded_file = "example_data.csv"
        df = load_data(uploaded_file)
    else:
        uploaded_file = st.file_uploader("Choose the data file (csv)", type="csv")
        df = load_data(uploaded_file) if uploaded_file is not None else None


if df is not None:
    df = _normalize_coordinates(df)
    df["X"] = pd.to_numeric(df["X"], errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"], errors="coerce")

    df["X"] = df["X"] % PLOT_SIZE_METERS
    df["Y"] = df["Y"] % PLOT_SIZE_METERS
    # Check for plots/subplots columns
    has_plots_subplots = False
    if df is not None:
        if ("Plots" in df.columns and "Subplots" in df.columns) or ("Plot" in df.columns and "SubPlot" in df.columns):
            has_plots_subplots = True
    
    # Determine plot options
    if has_plots_subplots:
        plots_options = sorted(df["PlotDisplay"].dropna().unique())
    else:
        plots_options = df[PLOTID_COL].unique() if (df is not None and PLOTID_COL in df.columns) else []
        if df is not None and PLOTID_COL not in df.columns and not has_plots_subplots:
            st.warning(f"Uploaded CSV does not contain a '{PLOTID_COL}' column or Plot/SubPlot columns. Plot selection is disabled.")
    
    with st.sidebar:
        if len(plots_options) > 0:
            selected_plot = st.selectbox("Select plot to display:", options=plots_options)
            # Convert PlotDisplay format ("1 - 1") to PlotID format ("1-1") if needed
            if has_plots_subplots and " - " in str(selected_plot):
                plot_id_filtered = selected_plot.replace(" - ", "-")
            else:
                plot_id_filtered = selected_plot
            # Filter dataframe to selected plot
            df = df[df[PLOTID_COL] == plot_id_filtered]
    
    try:
        colors = assign_colors(df[SPECIES_COL].unique())
        topcol1, topcol2, topcol3 = st.columns([2, 1, 2])
        
        with topcol1:
            plotting_group = st.selectbox("Pick attribute to plot trees by", 
                                         [SPECIES_COL, STATUS_COL, CROWN_COL])
        
        if "Year" in df.columns:  
            year_list = sorted(df["Year"].dropna().unique())
            with topcol2:
                year = st.pills("Pick Year to Plot Data", year_list, default=year_list[0])
        else:
            st.warning("No 'Year' column found in data.")
            year = None
        
        
        if year is not None:
            fn = plot_data(df, colors, plotting_group, year)
            

        species_counts = df[SPECIES_COL].value_counts().sort_values(ascending=False)
        with st.sidebar:
            st.write(df)
            diversity_plot(species_counts, colors)
            st.metric("Total trees:", len(df))
            st.metric("Unique Species", len(species_counts))
            dbh_app(df, colors)
            
        col1, col2, col3 = st.columns(3)
        with col1:
            if year is not None:
                st.write(DEFAULT_YEAR_TEXT_FORMAT.format(year))
        with col2:
            with open(fn, "rb") as img:
                st.download_button(
                    label="Download Figure",
                    data=img,
                    file_name=fn,
                    mime="image/png"
                )
        with col3:
            st.write("Created by Aidan Maddock")

    except ValueError as e:
        st.error(f"Data error: {e}")
    except Exception as e:
        st.error(f"Error during plotting: {e}. Refer to the troubleshooting section.")
    else:
        st.warning("Data could not be loaded. Check integrity of file.")