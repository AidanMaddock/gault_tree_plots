import streamlit as st
import sys, os
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, List
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Comparison")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tree_plots import load_data, normalize_coordinates, plot_data, assign_colors, load_species_dict, load_status_dict
from tree_statistics import compute_plot_year_stats, diversity, compute_dbh_increments, diversity_plot, dbh_plot

from config import (
    DIAMETER_COL, PLOT_SIZE_METERS, SPECIES_COL, STATUS_COL, CROWN_COL,
    PLOTID_COL, PLOT_AREA_M2, MATPLOTLIB_FIGSIZE_WIDE, MATPLOTLIB_FIGSIZE_SQUARE,
    COORD_X_ALIASES, COORD_Y_ALIASES, WELCOME_TEXT, DEFAULT_BINS, MIN_BINS, MAX_BINS,
    DEFAULT_YEAR_TEXT_FORMAT
)

def dbh_app(df: pd.DataFrame, colors: dict) -> None:
    """Display DBH histogram and statistics for a dataset."""
    species_list = sorted(df[SPECIES_COL].dropna().unique())
    species_options = ["Select All"] + list(species_list)
    selected = st.multiselect("Choose species:", options=species_options, default=["Select All"], key="dbh_species")

    if "Select All" in selected:
        selected_species = list(species_list)
    else:
        selected_species = selected

    filtered_df = df[df[SPECIES_COL].isin(selected_species)]
    
    num_bins = st.slider("Number of bins for DBH histogram", min_value=MIN_BINS, max_value=MAX_BINS, value=DEFAULT_BINS, key="dbh_bins")
    all_dbh = df[DIAMETER_COL].dropna()
    
    if len(all_dbh) == 0:
        st.warning("No DBH data available.")
        return
    
    bin_edges = np.histogram_bin_edges(all_dbh, bins=num_bins)
    one_colour = st.checkbox("Use Species-Specific Colouring", value=True, key="dbh_color")
    dbh_plot(filtered_df, selected_species, bin_edges, colors, one_colour)
    
    if selected_species:
        avg_dbh = filtered_df[DIAMETER_COL].mean()
        st.write(f"Mean {DIAMETER_COL}: {avg_dbh:.2f} cm")

# Title of page 
st.title("Tree Plot Grapher")
st.write(WELCOME_TEXT)
with st.sidebar:
    file_option = st.radio("Data source:", ["Upload your data", "See an example"], horizontal=True)
    
    if file_option == "See an example":
        uploaded_file = "Data/example_data.csv"
        df = load_data(uploaded_file)
        st.info("Showing example data from example_data.csv")
    else:
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
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

    
    use_control = False
    df_control = None
    control_plots_options = []
    control_selected = None
    has_control_plots_subplots = False
    
    
    use_control = st.checkbox("Compare with a control file", value=False)

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
        plots = st.multiselect("Select plot(s) to view:", options=plots_options, max_selections=2)

    plotting_group = st.selectbox("Pick attribute to plot trees by", [SPECIES_COL, STATUS_COL, CROWN_COL, None], format_func=lambda x: "No grouping (Grey)" if x is None else x)
    
    use_mapped_names = st.checkbox("Use full species/status names in legends", value=True)


if uploaded_file is not None and df is not None:
    df = normalize_coordinates(df)
    df["X"] = pd.to_numeric(df["X"], errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"], errors="coerce")

    df["X"] = df["X"] % PLOT_SIZE_METERS
    df["Y"] = df["Y"] % PLOT_SIZE_METERS
    if df_control is not None:
        df_control = normalize_coordinates(df_control)
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
    
    all_status = []
    if STATUS_COL in df.columns:
        all_status.extend(list(df[STATUS_COL].dropna().unique()))
    if df_control is not None and STATUS_COL in df_control.columns:
        all_status.extend(list(df_control[STATUS_COL].dropna().unique()))
    all_status = sorted(set(all_status))
    colorsstat = assign_colors(all_status)

    # Initialize subset variables for later use
    subset1 = None
    subset2 = None
    
    # Single plot cross-section view (only if NOT comparing with control)
    if len(plots) == 1 and not (use_control and control_selected is not None):
        selected_plot = plots[0]
        
        # Convert PlotDisplay format ("1 - 1") to PlotID format ("1-1") if needed
        if has_plots_subplots and " - " in str(selected_plot):
            plot_id_filtered = selected_plot.replace(" - ", "-")
        else:
            plot_id_filtered = selected_plot
        
        # Filter dataframe to selected plot
        df_subset = df[df[PLOTID_COL] == plot_id_filtered].copy()
        
        if df_subset.empty:
            st.warning(f"No data found for plot {selected_plot}")
        else:
            st.subheader(f"Cross Section - Plot {selected_plot}")
            
            try:
                # Year selection
                if "Year" in df_subset.columns:  
                    year_list = sorted(df_subset["Year"].dropna().unique())
                    year = st.pills("Pick Year to Plot Data", year_list, default=year_list[0])
                    
                    if year is not None:
                        year_subset = df_subset[df_subset["Year"] == year]
                        species_dict = load_species_dict() if use_mapped_names else {}
                        status_dict = load_status_dict() if use_mapped_names else {}
                        fn = plot_data(year_subset, colors, plotting_group, year, species_dict=species_dict, status_dict=status_dict)
                    
                    # Species statistics and DBH
                    col1, col2, col3 = st.columns([1, 0.5, 1])
                    
                    species_counts = df_subset[SPECIES_COL].value_counts().sort_values(ascending=False)
                    with col2:
                        st.metric("Total trees:", len(year_subset))
                        st.metric("Unique Species", len(species_counts))  
                        st.metric("Mean DBH (cm)", f"{df_subset[DIAMETER_COL].mean():.1f}")
                        st.metric("Median DBH (cm)", f"{df_subset[DIAMETER_COL].median():.1f}") 
                        top_species, top_count = species_counts.index[0], species_counts.iloc[0]
                        st.metric(
                            "Dominant Species (%)",
                            f"{top_species}:{100 * top_count / len(df_subset):.1f}%"
                        )
                                            
                    with col1:
                        with st.expander("Species Composition", expanded = True):
                            diversity_plot(species_counts, colors)
                    
                    with col3:
                        with st.expander("DBH Analysis", expanded=True):
                            dbh_app(df_subset, colors)
                    
                    # Download button
                    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
                    with col_dl1:
                        if year is not None and 'fn' in locals():
                            with open(fn, "rb") as img:
                                st.download_button(
                                    label="Download Figure",
                                    data=img,
                                    file_name=fn,
                                    mime="image/png",
                                    key="single_download"
                                )
                else:
                    st.warning("No 'Year' column found in data.")
            except Exception as e:
                st.error(f"Error processing plot: {str(e)}")
    
    # Comparison view (two plots)
    elif (not use_control and len(plots) == 2) or (use_control and len(plots) == 1 and control_selected is not None):
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
                        species_dict = load_species_dict() if use_mapped_names else {}
                        status_dict = load_status_dict() if use_mapped_names else {}
                        wn = plot_data(subset1, colors, plotting_group, year=year1, species_dict=species_dict, status_dict=status_dict)

                    
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
                        species_dict = load_species_dict() if use_mapped_names else {}
                        status_dict = load_status_dict() if use_mapped_names else {}
                        rn = plot_data(subset2, colors, plotting_group, year=year2, species_dict=species_dict, status_dict=status_dict)

                    
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
                rows=5, cols=2,
                specs=[
                    [{"colspan": 2}, None],   # row 1: density
                    [{"colspan": 2}, None],   # row 2: basal area
                    [{}, {}],                 # row 3: species
                    [{}, {}],                  # row 4: status
                    [{"colspan": 2}, None],   # row 5: DBH histogram
                ],
                subplot_titles=(
                    "Tree density over time",
                    "Basal area (m²) over time",
                    f"Species composition: Plot {plotA}",
                    f"Species composition: Plot {plotB}",
                    f"Status composition: Plot {plotA}",
                    f"Status composition: Plot {plotB}",
                ),
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

            status_mapping = {s: colors[s] for s in (all_status if len(all_status) > 0 else df[STATUS_COL].dropna().unique())}

            a_status = stats_a['status_df']
            b_status = stats_b['status_df']

            piv_as = a_status.pivot(index='Year', columns=STATUS_COL, values='Proportion').fillna(0).sort_index()
            piv_bs = b_status.pivot(index='Year', columns=STATUS_COL, values='Proportion').fillna(0).sort_index()

            for ap in piv_as.columns:
                fig.add_trace(go.Scatter(x=piv_as.index, y=piv_as[ap], name=str(ap), legendgroup=str(ap), 
                                        showlegend=False, stackgroup='one', mode='none', 
                                        fillcolor=status_mapping.get(ap)), row=4, col=1)

            for ap in piv_bs.columns:
                fig.add_trace(go.Scatter(x=piv_bs.index, y=piv_bs[ap], name=str(ap), legendgroup=str(ap), 
                                        showlegend=False, stackgroup='two', mode='none', 
                                        fillcolor=status_mapping.get(ap)), row=4, col=2)
                

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
                                              nbinsx=len(bins)-1, marker_color='rgba(31,119,180,0.6)', opacity=0.7), row=5, col=1)
                    fig.add_trace(go.Histogram(x=subset2[DIAMETER_COL], name=f"{DIAMETER_COL} {plotB}", 
                                              nbinsx=len(bins)-1, marker_color='rgba(255,127,14,0.6)', opacity=0.7), row=5, col=1)
                    fig.update_xaxes(title_text=f'{DIAMETER_COL} (cm)', row=5, col=1)
                    fig.update_yaxes(title_text='Count', row=5, col=1)

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

col1, col2, col3 = st.columns([1,2,1])
with col1:
    if uploaded_file is not None:
        try:
            if year1 is not None and 'wn' in locals():
                with open(wn, "rb") as img:
                    st.download_button(
                        label="Download Figure 1",
                        data=img,
                        file_name=wn,
                        mime="image/png",
                        key="compare_download"
                    )
            if year2 is not None and 'rn' in locals():
                with open(rn, "rb") as img:
                    st.download_button(
                        label="Download Figure 2",
                        data=img,
                        file_name=rn,
                        mime="image/png",
                        key="comp_download"
                    )
        except:
            pass
