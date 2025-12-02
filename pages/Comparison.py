import streamlit as st
st.set_page_config(layout="wide", page_title="Comparison")
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tree_plots import load_data, plot_data, assign_colors


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
    plots = st.multiselect("Select two plots to compare:", options=plots_options, max_selections = 2)

    # Allow filtering by year if year column exists for specific plots
    plotting_group = st.selectbox("Pick attribute to plot trees by", [SPECIES_COL, STATUS_COL, CROWN_COL])



if uploaded_file is not None and df is not None:
    # standardize coords and strip whitespace from header names done in load_data
    df = df.rename(columns={"CoorX": "X", "CoorY": "Y"})
    # Build a shared color mapping across both plots so species colors are consistent
    colors = assign_colors(df[SPECIES_COL].unique() if SPECIES_COL in df.columns else [])
    
    if len(plots) == 2:
            col1, col2 = st.columns(2)

            for i, plot_id in enumerate(plots):
                subset = df[df["PlotID"] == plot_id]
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

import seaborn as sns

# Only create the comparison chart if the data has the required columns
if df is not None and all(c in df.columns for c in ["Year", "value" "PlotID"]):
    fig, ax = plt.subplots(figsize=(10,6))
    sns.lineplot(data=df, x="Year", y="Value", hue="PlotID", ax=ax)
    st.pyplot(fig)
else:
    st.info("Comparison chart requires a DataFrame with 'Year', 'Value', and 'PlotID' columns. Upload an appropriate CSV to view this chart.")