import streamlit as st
st.set_page_config(layout="wide", page_title="Comparison")
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tree_plots import load_data, plot_data, assign_colors
import numpy as np
from tree_statistics import compute_plot_year_stats, diversity, compute_dbh_increments
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List
import pandas as pd

from config import (
    DIAMETER_COL, PLOT_SIZE_METERS, SPECIES_COL, STATUS_COL, CROWN_COL,
    PLOTID_COL, PLOT_AREA_M2, MATPLOTLIB_FIGSIZE_WIDE,
    COORD_X_ALIASES, COORD_Y_ALIASES
)

def _normalize_coordinates(df: pd.DataFrame) -> pd.DataFrame:
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

    for col in df.columns:
        if 'plot' in col.lower():
            df[col] = df[col].astype(str).str.replace('\u00A0', ' ')  # NBSP -> space
            df[col] = df[col].str.strip()
            df[col] = df[col].str.replace(r'\s*-\s*', '-', regex=True)
    
    return df

st.title("Tree Plot Comparison")

with st.sidebar:
    file_option = st.radio("Data source:", ["Upload your data", "See an example"], horizontal=True)
    
    if file_option == "See an example":
        uploaded_file = "example_data.csv"
        df = load_data(uploaded_file)
        st.info("Showing example data from example_data.csv")
    else:
        uploaded_file = st.file_uploader("Choose a data file containing all data. Must include a PlotID column", type="csv")
        df = load_data(uploaded_file) if uploaded_file is not None else None
    
    has_plots_subplots = False
    
    if df is not None:
        
        if ("Plots" in df.columns and "Subplots" in df.columns) or ("Plot" in df.columns and "SubPlot" in df.columns):
            has_plots_subplots = True
    
    if has_plots_subplots:
        plots_options = sorted(df["PlotDisplay"].dropna().unique())
    else:
        plots_options = df[PLOTID_COL].unique() if (df is not None and PLOTID_COL in df.columns) else []
        if df is not None and PLOTID_COL not in df.columns and not has_plots_subplots:
            st.warning(f"Uploaded CSV does not contain a '{PLOTID_COL}' column or Plot/SubPlot columns. Plot selection is disabled.")

    use_control = st.checkbox("Compare with a control file", value=False)
    df_control = None
    control_plots_options = []
    control_selected = None
    has_control_plots_subplots = False

    if use_control:
        control_file = st.file_uploader("Upload a control file to compare against", type="csv", key="control_file")
        df_control = load_data(control_file) if control_file is not None else None
        
        if df_control is not None:
            if ("Plots" in df_control.columns and "Subplots" in df_control.columns) or ("Plot" in df_control.columns and "SubPlot" in df_control.columns):
                has_control_plots_subplots = True
        
        if has_control_plots_subplots:
            control_plots_options = sorted(df_control["PlotDisplay"].dropna().unique())
        else:
            control_plots_options = df_control[PLOTID_COL].unique() if (df_control is not None and PLOTID_COL in df_control.columns) else []
            if df_control is not None and PLOTID_COL not in df_control.columns and not has_control_plots_subplots:
                st.warning(f"Control CSV does not contain a '{PLOTID_COL}' column or Plot/SubPlot columns. Control plot selection is disabled.")

    if use_control:
        plots = st.multiselect("Select plot to compare (main file)", options=plots_options, max_selections=1)
        control_selected = st.selectbox("Select the control plot to compare against", options=control_plots_options) if df_control is not None else None
    else:
        plots = st.multiselect("Select two plots to compare:", options=plots_options, max_selections=2)

    plotting_group = st.selectbox("Pick attribute to plot trees by", [SPECIES_COL, STATUS_COL, CROWN_COL])


if uploaded_file is not None and df is not None:
    df = _normalize_coordinates(df)
    df["X"] = pd.to_numeric(df["X"], errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"], errors="coerce")

    df["X"] = df["X"] % PLOT_SIZE_METERS
    df["Y"] = df["Y"] % PLOT_SIZE_METERS
    if df_control is not None:
        df_control = _normalize_coordinates(df_control)
        df_control["X"] = pd.to_numeric(df_control["X"], errors="coerce")
        df_control["Y"] = pd.to_numeric(df_control["Y"], errors="coerce")
        df_control["X"] = df_control["X"] % PLOT_SIZE_METERS
        df_control["Y"] = df_control["Y"] % PLOT_SIZE_METERS

    all_species = []
    if SPECIES_COL in df.columns:
        all_species.extend(list(df[SPECIES_COL].dropna().unique()))
    if df_control is not None and SPECIES_COL in df_control.columns:
        all_species.extend(list(df_control[SPECIES_COL].dropna().unique()))
    all_species = sorted(set(all_species))
    colors = assign_colors(all_species)
    
    if (not use_control and len(plots) == 2) or (use_control and len(plots) == 1 and control_selected is not None):
        col1, col2 = st.columns(2)

        datasets = []
        plot_ids = []
        plot_labels = []
        
        if use_control:
            plot_ids = [plots[0], control_selected]
            datasets = [df, df_control]
        else:
            plot_ids = plots
            datasets = [df, df]

        subset1 = None
        subset2 = None
        for i, plot_id in enumerate(plot_ids):
            # Convert PlotDisplay format ("1 - 1") to PlotID format ("1-1") if needed
            # Use the appropriate has_plots_subplots flag based on which dataset we're using
            if i == 0:
                should_convert = has_plots_subplots
            else:  # i == 1
                should_convert = has_control_plots_subplots if use_control else has_plots_subplots
            
            if should_convert and " - " in str(plot_id):
                plot_id_filtered = plot_id.replace(" - ", "-")
            else:
                plot_id_filtered = plot_id
            
            subset = datasets[i][datasets[i][PLOTID_COL] == plot_id_filtered]
            label_id = plot_id

            if i == 0:
                with col1:
                    if subset.empty:
                        st.warning(f"No data found for {label_id}")
                        year1 = None
                    else:
                        available_years = sorted(subset["Year"].dropna().unique())
                        year1 = st.selectbox("Select year to display", options=available_years, key=1)
                    if year1:
                        subset1 = subset[subset["Year"] == year1]
                    st.subheader(f"Plot {label_id}")
                    if subset1 is not None and not subset1.empty:
                        plot_data(subset1, colors, plotting_group, year=year1)
            else:
                with col2:
                    if subset.empty:
                        st.warning(f"No data found for {label_id}")
                        year2 = None
                    else:
                        available_years = sorted(subset["Year"].dropna().unique())
                        year2 = st.selectbox("Select year to display", options=available_years, key=2)
                    if year2:
                        subset2 = subset[subset["Year"] == year2]
                    st.subheader(f"Plot {label_id}")
                    if subset2 is not None and not subset2.empty:
                        plot_data(subset2, colors, plotting_group, year=year2)

    #metric = st.selectbox("Choose a metric:", ["Tree density", "Basal area", "Species composition", "Survival"])
    
    if (not use_control and len(plots) == 2) or (use_control and len(plots) == 1 and control_selected is not None):
        if use_control:
            plotA, plotB = plots[0], control_selected
        else:
            plotA, plotB = plots[0], plots[1]
        
        if has_plots_subplots:
            plotA_id = plotA.replace(" - ", "-") if " - " in plotA else plotA
            stats_a = compute_plot_year_stats(df, plotA_id)
        else:
            stats_a = compute_plot_year_stats(df, plotA)
        
        if use_control and has_control_plots_subplots:
            plotB_id = plotB.replace(" - ", "-") if " - " in plotB else plotB
            stats_b = compute_plot_year_stats(df_control, plotB_id)
        elif use_control:
            df_b = df_control if df_control is not None else df
            stats_b = compute_plot_year_stats(df_b, plotB)
        else:
            # When not using control and has_plots_subplots, apply same conversion as plotA
            if has_plots_subplots:
                plotB_id = plotB.replace(" - ", "-") if " - " in plotB else plotB
                stats_b = compute_plot_year_stats(df, plotB_id)
            else:
                stats_b = compute_plot_year_stats(df, plotB)

        if stats_a is None or stats_b is None:
            st.warning("One or both selected plots do not have time-based data for statistics.")
        else:
            fig = make_subplots(
                rows=4, cols=2,
                specs=[[{"colspan": 2}, None], [{"colspan": 2}, None], [{}, {}], [{"colspan": 2}, None]],
                subplot_titles=("Tree density over time", "Basal area (m²) over time", 
                               f"Species composition: {plotA}", f"Species composition: {plotB}", "DBH Distribution")
            )

            a_counts = stats_a['counts_df'].sort_values('Year')
            b_counts = stats_b['counts_df'].sort_values('Year')
            fig.add_trace(go.Scatter(x=a_counts['Year'], y=a_counts['Count'] / PLOT_AREA_M2, 
                                    name=f"Density {plotA}", mode='lines+markers'), row=1, col=1)
            fig.add_trace(go.Scatter(x=b_counts['Year'], y=b_counts['Count'] / PLOT_AREA_M2, 
                                    name=f"Density {plotB}", mode='lines+markers'), row=1, col=1)

            a_ba = stats_a['basal_area_df'].sort_values('Year')
            b_ba = stats_b['basal_area_df'].sort_values('Year')
            fig.add_trace(go.Scatter(x=a_ba['Year'], y=a_ba['BasalArea_m2'], 
                                    name=f"Basal area - {plotA}", mode='lines+markers'), row=2, col=1)
            fig.add_trace(go.Scatter(x=b_ba['Year'], y=b_ba['BasalArea_m2'], 
                                    name=f"Basal area - {plotB}", mode='lines+markers'), row=2, col=1)

            species_mapping = {s: colors[s] for s in (all_species if len(all_species) > 0 else df[SPECIES_COL].dropna().unique())}

            a_species = stats_a['species_df']
            b_species = stats_b['species_df']
            piv_a = a_species.pivot(index='Year', columns=SPECIES_COL, values='Proportion').fillna(0).sort_index()
            piv_b = b_species.pivot(index='Year', columns=SPECIES_COL, values='Proportion').fillna(0).sort_index()

            for sp in piv_a.columns:
                fig.add_trace(go.Scatter(x=piv_a.index, y=piv_a[sp], name=str(sp), legendgroup=str(sp), 
                                        showlegend=True, stackgroup='one', mode='none', 
                                        fillcolor=species_mapping.get(sp)), row=3, col=1)

            for sp in piv_b.columns:
                fig.add_trace(go.Scatter(x=piv_b.index, y=piv_b[sp], name=str(sp), legendgroup=str(sp), 
                                        showlegend=False, stackgroup='two', mode='none', 
                                        fillcolor=species_mapping.get(sp)), row=3, col=2)

            fig.update_layout(title_text=f"Comparison Statistics: Plot {plotA} vs {plotB}", height=1000, showlegend=True)
            fig.update_xaxes(title_text='Year', row=3, col=1)
            fig.update_xaxes(title_text='Year', row=3, col=2)
            fig.update_yaxes(title_text='Count (per m²)', row=1, col=1)
            fig.update_yaxes(title_text='Basal area (m²)', row=2, col=1)

            if subset1 is not None and subset2 is not None:
                all_dbh = list(subset1[DIAMETER_COL].dropna().values) + list(subset2[DIAMETER_COL].dropna().values)
                if len(all_dbh) > 0:
                    bins = np.histogram_bin_edges(all_dbh, bins='auto')
                    fig.add_trace(go.Histogram(x=subset1[DIAMETER_COL], name=f"{DIAMETER_COL} {plotA}", 
                                              nbinsx=len(bins)-1, marker_color='rgba(31,119,180,0.6)', opacity=0.7), row=4, col=1)
                    fig.add_trace(go.Histogram(x=subset2[DIAMETER_COL], name=f"{DIAMETER_COL} {plotB}", 
                                              nbinsx=len(bins)-1, marker_color='rgba(255,127,14,0.6)', opacity=0.7), row=4, col=1)
                    fig.update_xaxes(title_text=f'{DIAMETER_COL} (cm)', row=4, col=1)
                    fig.update_yaxes(title_text='Count', row=4, col=1)

            st.plotly_chart(fig, use_container_width=True)

            total_ba_a = a_ba['BasalArea_m2'].sum()
            total_ba_b = b_ba['BasalArea_m2'].sum()
            avg_count_a = a_counts['Count'].mean() if not a_counts.empty else 0
            avg_count_b = b_counts['Count'].mean() if not b_counts.empty else 0
            
            if has_plots_subplots:
                plotA_id = plotA.replace(" - ", "-") if " - " in plotA else plotA
                div_a = diversity(df[df["PlotID"] == plotA_id])
            else:
                div_a = diversity(df[df[PLOTID_COL] == plotA])
            
            if use_control and has_control_plots_subplots:
                plotB_id = plotB.replace(" - ", "-") if " - " in plotB else plotB
                div_b = diversity(df_control[df_control["PlotID"] == plotB_id])
            elif use_control:
                df_b = df_control if df_control is not None else df
                div_b = diversity(df_b[df_b[PLOTID_COL] == plotB])
            else:
                if has_plots_subplots:
                    plotB_id = plotB.replace(" - ", "-") if " - " in plotB else plotB
                    div_b = diversity(df[df["PlotID"] == plotB_id])
                else:
                    div_b = diversity(df[df[PLOTID_COL] == plotB])

            if has_plots_subplots:
                plotA_id = plotA.replace(" - ", "-") if " - " in plotA else plotA
                inc_a = compute_dbh_increments(df, plotA_id)
            else:
                inc_a = compute_dbh_increments(df, plotA)
            
            if use_control and has_control_plots_subplots:
                plotB_id = plotB.replace(" - ", "-") if " - " in plotB else plotB
                inc_b = compute_dbh_increments(df_control, plotB_id)
            elif use_control:
                df_b = df_control if df_control is not None else df
                inc_b = compute_dbh_increments(df_b, plotB)
            else:
                if has_plots_subplots:
                    plotB_id = plotB.replace(" - ", "-") if " - " in plotB else plotB
                    inc_b = compute_dbh_increments(df, plotB_id)
                else:
                    inc_b = compute_dbh_increments(df, plotB)
            
            mean_inc_a = np.nanmean(inc_a) if inc_a is not None and len(inc_a) > 0 else 0
            mean_inc_b = np.nanmean(inc_b) if inc_b is not None and len(inc_b) > 0 else 0

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(label=f"Average trees ({plotA})", value=f"{avg_count_a:.1f}")
                st.metric(label=f"Total Basal Area ({plotA})", value=f"{total_ba_a:.2f} m²")
                st.metric(label=f"Species richness ({plotA})", value=f"{div_a}")
                st.metric(label=f"Mean {DIAMETER_COL} increment ({plotA})", value=f"{mean_inc_a:.2f} cm/yr")
            with col_b:
                st.metric(label=f"Average trees ({plotB})", value=f"{avg_count_b:.1f}")
                st.metric(label=f"Total Basal Area ({plotB})", value=f"{total_ba_b:.2f} m²")
                st.metric(label=f"Species richness ({plotB})", value=f"{div_b}")
                st.metric(label=f"Mean {DIAMETER_COL} increment ({plotB})", value=f"{mean_inc_b:.2f} cm/yr")