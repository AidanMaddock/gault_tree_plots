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


DIAMETER_COL = "DBH"
SPECIES_COL = "Species"
OUTPUT_PATH = "output.png"
CROWN_COL = "CrownClass"
STATUS_COL = "Status"


st.title("Tree Plot Comparison")

with st.sidebar:
    uploaded_file = st.file_uploader("Choose a data file containing all data. Must include a plotID column", type="csv")
    df = load_data(uploaded_file)
    # Default empty list if df is None or does not contain PlotID
    plots_options = df["PlotID"].unique() if (df is not None and "PlotID" in df.columns) else []
    if df is not None and "PlotID" not in df.columns:
        st.warning("Uploaded CSV does not contain a 'PlotID' column. Plot selection is disabled.")

    # Checkbox to enable control file comparison
    use_control = st.checkbox("Compare with a control file", value=False)
    df_control = None
    control_plots_options = []
    control_selected = None

    # Show control upload only if checkbox is checked
    if use_control:
        control_file = st.file_uploader("Upload a control file to compare against", type="csv", key="control_file")
        df_control = load_data(control_file) if control_file is not None else None
        control_plots_options = df_control["PlotID"].unique() if (df_control is not None and "PlotID" in df_control.columns) else []
        if df_control is not None and "PlotID" not in df_control.columns:
            st.warning("Control CSV does not contain a 'PlotID' column. Control plot selection is disabled.")

    if use_control:
        plots = st.multiselect("Select plot to compare (main file)", options=plots_options, max_selections=1)
        control_selected = st.selectbox("Select the control plot to compare against", options=control_plots_options) if df_control is not None else None
    else:
        plots = st.multiselect("Select two plots to compare:", options=plots_options, max_selections = 2)

    # Allow filtering by year if year column exists for specific plots
    plotting_group = st.selectbox("Pick attribute to plot trees by", [SPECIES_COL, STATUS_COL, CROWN_COL])



if uploaded_file is not None and df is not None:
    # standardize coords and strip whitespace from header names done in load_data
    df = df.rename(columns={"CoorX": "X", "CoorY": "Y"})
    if df_control is not None:
        df_control = df_control.rename(columns={"CoorX": "X", "CoorY": "Y"})

    # Build a shared color mapping across both main and control files so species colors are consistent
    all_species = []
    if SPECIES_COL in df.columns:
        all_species.extend(list(df[SPECIES_COL].dropna().unique()))
    if df_control is not None and SPECIES_COL in df_control.columns:
        all_species.extend(list(df_control[SPECIES_COL].dropna().unique()))
    # Use unique species
    all_species = sorted(set(all_species))
    colors = assign_colors(all_species)
    
    if (not use_control and len(plots) == 2) or (use_control and len(plots) == 1 and control_selected is not None):
            col1, col2 = st.columns(2)

            # Determine datasets for left and right panels
            datasets = []
            plot_ids = []
            if use_control:
                plot_ids = [plots[0], control_selected]
                datasets = [df, df_control]
            else:
                plot_ids = plots
                datasets = [df, df]

            # initialize placeholders for selected subsets (used later for histogram)
            subset1 = None
            subset2 = None
            for i, plot_id in enumerate(plot_ids):
                subset = datasets[i][datasets[i]["PlotID"] == plot_id]
                # use shared colors mapping computed above
                # colors = assign_colors(subset[SPECIES_COL].unique())

                if i == 0:
                    with col1:
                        year1 = st.selectbox("Select year to display", options=sorted(subset["Year"].dropna().unique()), key = 1)
                        if year1:
                            subset1 = subset[subset["Year"] == year1]
                        st.subheader(f"Plot {plot_id}")
                        plot_data(subset1, colors, plotting_group, year=year1)
                else:
                    with col2:
                        year2 = st.selectbox("Select year to display", options=sorted(subset["Year"].dropna().unique()), key = 2)
                        if year2:
                            subset2 = subset[subset["Year"] == year2]
                        st.subheader(f"Plot {plot_id}")
                        plot_data(subset2, colors, plotting_group, year=year2)

    #Comparison Statistics 
    metric = st.selectbox("Choose a metric:", ["Tree density", "Basal area", "Species composition", "Survival"])
    # If we have two plots, or using control with a selected control plot, compute time-series stats and build Plotly comparison figure
    if (not use_control and len(plots) == 2) or (use_control and len(plots) == 1 and control_selected is not None):
            # Determine plot IDs
            if use_control:
                plotA, plotB = plots[0], control_selected
            else:
                plotA, plotB = plots[0], plots[1]
            stats_a = compute_plot_year_stats(df, plotA)
            stats_b = compute_plot_year_stats(df_control if (use_control and df_control is not None) else df, plotB)

            if stats_a is None or stats_b is None:
                st.warning("One or both selected plots do not have time-based data for statistics.")
            else:
                # Build Plotly combined figure: Density (row1), Basal Area (row2), Species composition (row3 split into two columns), DBH histogram (row4)
                fig = make_subplots(
                    rows=4, cols=2,
                    specs=[[{"colspan": 2}, None], [{"colspan": 2}, None], [{}, {}], [{"colspan": 2}, None]],
                    subplot_titles=("Tree density over time", "Basal area (m^2) over time", f"Species composition: {plotA}", f"Species composition: {plotB}", "DBH Distribution")
                )

                # Density traces
                a_counts = stats_a['counts_df'].sort_values('Year')
                b_counts = stats_b['counts_df'].sort_values('Year')
                fig.add_trace(go.Scatter(x=a_counts['Year'], y=a_counts['Count'] / 400, name=f"Density per M²", mode='lines+markers'), row=1, col=1)
                fig.add_trace(go.Scatter(x=b_counts['Year'], y=b_counts['Count'] / 400, name=f"Density per M²", mode='lines+markers'), row=1, col=1)

                # Basal area traces
                a_ba = stats_a['basal_area_df'].sort_values('Year')
                b_ba = stats_b['basal_area_df'].sort_values('Year')
                fig.add_trace(go.Scatter(x=a_ba['Year'], y=a_ba['BasalArea_m2'], name=f"Basal area - {plotA}", mode='lines+markers'), row=2, col=1)
                fig.add_trace(go.Scatter(x=b_ba['Year'], y=b_ba['BasalArea_m2'], name=f"Basal area - {plotB}", mode='lines+markers'), row=2, col=1)

                # Species composition stacked area plots per plot
                # Use shared color mapping so the same species uses the same color across plots
                species_mapping = {s: colors[s] for s in (all_species if len(all_species) > 0 else df[SPECIES_COL].dropna().unique())}

                # Prepare pivoted species proportion per year for each plot
                a_species = stats_a['species_df']
                b_species = stats_b['species_df']
                piv_a = a_species.pivot(index='Year', columns='Species', values='Proportion').fillna(0).sort_index()
                piv_b = b_species.pivot(index='Year', columns='Species', values='Proportion').fillna(0).sort_index()

                # Add area traces for Plot A (left bottom)
                for sp in piv_a.columns:
                    fig.add_trace(go.Scatter(x=piv_a.index, y=piv_a[sp], name=str(sp), legendgroup=str(sp), showlegend=True, stackgroup='one', mode='none', fillcolor=species_mapping.get(sp)), row=3, col=1)

                # Add area traces for Plot B (right bottom) using a different stackgroup
                for sp in piv_b.columns:
                    fig.add_trace(go.Scatter(x=piv_b.index, y=piv_b[sp], name=str(sp), legendgroup=str(sp), showlegend=False, stackgroup='two', mode='none', fillcolor=species_mapping.get(sp)), row=3, col=2)

                fig.update_layout(title_text=f"Comparison Statistics: Plot {plotA} vs {plotB}", height=1000, showlegend=True)
                fig.update_xaxes(title_text='Year', row=3, col=1)
                fig.update_xaxes(title_text='Year', row=3, col=2)
                fig.update_yaxes(title_text='Count', row=1, col=1)
                fig.update_yaxes(title_text='Basal area (m^2)', row=2, col=1)
                # We'll render the final fig (including histogram) later

                # Add DBH histogram for the selected years (if we have the subsets)
                if subset1 is not None and subset2 is not None:
                    # Use consistent binning across both histograms
                    all_dbh = list(subset1['DBH'].dropna().values) + list(subset2['DBH'].dropna().values)
                    if len(all_dbh) > 0:
                        bins = np.histogram_bin_edges(all_dbh, bins='auto')
                        fig.add_trace(go.Histogram(x=subset1['DBH'], name=f"DBH {plotA}", nbinsx=len(bins)-1, marker_color='rgba(31,119,180,0.6)', opacity=0.7), row=4, col=1)
                        fig.add_trace(go.Histogram(x=subset2['DBH'], name=f"DBH {plotB}", nbinsx=len(bins)-1, marker_color='rgba(255,127,14,0.6)', opacity=0.7), row=4, col=1)
                        fig.update_xaxes(title_text='DBH (cm)', row=4, col=1)
                        fig.update_yaxes(title_text='Count', row=4, col=1)

                st.plotly_chart(fig, use_container_width=True)

                # Small comparative metrics
                total_ba_a = a_ba['BasalArea_m2'].sum()
                total_ba_b = b_ba['BasalArea_m2'].sum()
                avg_count_a = a_counts['Count'].mean() if not a_counts.empty else 0
                avg_count_b = b_counts['Count'].mean() if not b_counts.empty else 0
                # compute diversity metrics using the correct dataset for plotB if it's from the control file
                div_a = diversity(df[df['PlotID'] == plotA])
                div_b = diversity((df_control if (use_control and df_control is not None) else df)[(df_control if (use_control and df_control is not None) else df)['PlotID'] == plotB])

                # Compute mean annual DBH increments
                inc_a = compute_dbh_increments(df, plotA)
                inc_b = compute_dbh_increments((df_control if (use_control and df_control is not None) else df), plotB)
                mean_inc_a = np.nanmean(inc_a) if inc_a is not None and len(inc_a) > 0 else 0
                mean_inc_b = np.nanmean(inc_b) if inc_b is not None and len(inc_b) > 0 else 0

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric(label=f"Average trees ({plotA})", value=f"{avg_count_a:.1f}")
                    st.metric(label=f"Total Basal Area ({plotA})", value=f"{total_ba_a:.2f} m^2")
                    st.metric(label=f"Species richness ({plotA})", value=f"{div_a}")
                    st.metric(label=f"Mean DBH increment ({plotA})", value=f"{mean_inc_a:.2f} cm/yr")
                with col_b:
                    st.metric(label=f"Average trees ({plotB})", value=f"{avg_count_b:.1f}")
                    st.metric(label=f"Total Basal Area ({plotB})", value=f"{total_ba_b:.2f} m^2")
                    st.metric(label=f"Species richness ({plotB})", value=f"{div_b}")
                    st.metric(label=f"Mean DBH increment ({plotB})", value=f"{mean_inc_b:.2f} cm/yr")

import seaborn as sns

# Only create the comparison chart if the data has the required columns
if df is not None and all(c in df.columns for c in ["Year", "Value", "PlotID"]):
    # Keep the existing seaborn style chart for a generic 'Value' column if present
    fig, ax = plt.subplots(figsize=(10,6))
    sns.lineplot(data=df, x="Year", y="Value", hue="PlotID", ax=ax)
    st.pyplot(fig)
else:
    st.info("Comparison chart requires a DataFrame with 'Year', 'Value', and 'PlotID' columns to display the default comparison chart. Uploaded CSV can still show density/basal composition if PlotID is present.")