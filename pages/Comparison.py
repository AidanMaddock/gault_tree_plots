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
    DIAMETER_COL, SPECIES_COL, STATUS_COL, CROWN_COL,
    PLOTID_COL, PLOT_AREA_M2, MATPLOTLIB_FIGSIZE_WIDE,
    COORD_X_ALIASES, COORD_Y_ALIASES
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
    plots_options = df[PLOTID_COL].unique() if (df is not None and PLOTID_COL in df.columns) else []
    if df is not None and PLOTID_COL not in df.columns:
        st.warning(f"Uploaded CSV does not contain a '{PLOTID_COL}' column. Plot selection is disabled.")

    use_control = st.checkbox("Compare with a control file", value=False)
    df_control = None
    control_plots_options = []
    control_selected = None

    if use_control:
        control_file = st.file_uploader("Upload a control file to compare against", type="csv", key="control_file")
        df_control = load_data(control_file) if control_file is not None else None
        control_plots_options = df_control[PLOTID_COL].unique() if (df_control is not None and PLOTID_COL in df_control.columns) else []
        if df_control is not None and PLOTID_COL not in df_control.columns:
            st.warning(f"Control CSV does not contain a '{PLOTID_COL}' column. Control plot selection is disabled.")

    if use_control:
        plots = st.multiselect("Select plot to compare (main file)", options=plots_options, max_selections=1)
        control_selected = st.selectbox("Select the control plot to compare against", options=control_plots_options) if df_control is not None else None
    else:
        plots = st.multiselect("Select two plots to compare:", options=plots_options, max_selections=2)

    plotting_group = st.selectbox("Pick attribute to plot trees by", [SPECIES_COL, STATUS_COL, CROWN_COL])
    show_heatmap = st.checkbox("Show heatmap overlay", value=False)

if uploaded_file is not None and df is not None:
    df = _normalize_coordinates(df)
    if df_control is not None:
        df_control = _normalize_coordinates(df_control)

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
        if use_control:
            plot_ids = [plots[0], control_selected]
            datasets = [df, df_control]
        else:
            plot_ids = plots
            datasets = [df, df]

        subset1 = None
        subset2 = None
        for i, plot_id in enumerate(plot_ids):
            subset = datasets[i][datasets[i][PLOTID_COL] == plot_id]

            if i == 0:
                with col1:
                    year1 = st.selectbox("Select year to display", options=sorted(subset["Year"].dropna().unique()), key=1)
                    if year1:
                        subset1 = subset[subset["Year"] == year1]
                    st.subheader(f"Plot {plot_id}")
                    if subset1 is not None:
                        if show_heatmap:
                            fig_heat = go.Figure()
                            fig_heat.add_trace(go.Histogram2d(
                                x=subset1["X"],
                                y=subset1["Y"],
                                colorscale="YlOrRd",
                                opacity=0.5,
                                xbins=dict(start=0, end=20, size=1),
                                ybins=dict(start=0, end=20, size=1),
                                showscale=True,
                                name="Density Heatmap"
                            ))
                            fig_heat.add_trace(go.Scatter(
                                x=subset1["X"],
                                y=subset1["Y"],
                                mode="markers",
                                marker=dict(size=subset1[DIAMETER_COL] * 0.8, color="blue", opacity=0.7),
                                text=subset1[SPECIES_COL],
                                name="Trees"
                            ))
                            fig_heat.update_layout(
                                title=f"Plot {plot_id} ({year1}) with Heatmap",
                                xaxis=dict(range=[0, 20], title="X"),
                                yaxis=dict(range=[0, 20], title="Y"),
                                height=400
                            )
                            st.plotly_chart(fig_heat, use_container_width=True)
                        else:
                            plot_data(subset1, colors, plotting_group, year=year1)
            else:
                with col2:
                    year2 = st.selectbox("Select year to display", options=sorted(subset["Year"].dropna().unique()), key=2)
                    if year2:
                        subset2 = subset[subset["Year"] == year2]
                    st.subheader(f"Plot {plot_id}")
                    if subset2 is not None:
                        if show_heatmap:
                            fig_heat = go.Figure()
                            fig_heat.add_trace(go.Histogram2d(
                                x=subset2["X"],
                                y=subset2["Y"],
                                colorscale="YlOrRd",
                                opacity=0.5,
                                xbins=dict(start=0, end=20, size=1),
                                ybins=dict(start=0, end=20, size=1),
                                showscale=True,
                                name="Density Heatmap"
                            ))
                            fig_heat.add_trace(go.Scatter(
                                x=subset2["X"],
                                y=subset2["Y"],
                                mode="markers",
                                marker=dict(size=subset2[DIAMETER_COL] * 0.8, color="blue", opacity=0.7),
                                text=subset2[SPECIES_COL],
                                name="Trees"
                            ))
                            fig_heat.update_layout(
                                title=f"Plot {plot_id} ({year2}) with Heatmap",
                                xaxis=dict(range=[0, 20], title="X"),
                                yaxis=dict(range=[0, 20], title="Y"),
                                height=400
                            )
                            st.plotly_chart(fig_heat, use_container_width=True)
                        else:
                            plot_data(subset2, colors, plotting_group, year=year2)

    #metric = st.selectbox("Choose a metric:", ["Tree density", "Basal area", "Species composition", "Survival"])
    
    if (not use_control and len(plots) == 2) or (use_control and len(plots) == 1 and control_selected is not None):
        if use_control:
            plotA, plotB = plots[0], control_selected
        else:
            plotA, plotB = plots[0], plots[1]
        
        stats_a = compute_plot_year_stats(df, plotA)
        stats_b = compute_plot_year_stats(df_control if (use_control and df_control is not None) else df, plotB)

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
            
            div_a = diversity(df[df[PLOTID_COL] == plotA])
            df_b = df_control if (use_control and df_control is not None) else df
            div_b = diversity(df_b[df_b[PLOTID_COL] == plotB])

            inc_a = compute_dbh_increments(df, plotA)
            inc_b = compute_dbh_increments(df_b, plotB)
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