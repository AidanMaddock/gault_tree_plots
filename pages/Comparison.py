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
STATUS_COL = "Status "


st.title("Tree Plot Comparison")

with st.sidebar:
    uploaded_file = st.file_uploader("Choose a data file containing all data. Must include a plotID column", type="csv")
    df = load_data(uploaded_file)
    plots = st.multiselect("Select two plots to compare:", options=df["PlotID"].unique(), max_selections = 2)

    # Allow filtering by year if year column exists for specific plots
    plotting_group = st.selectbox("Pick attribute to plot trees by", [SPECIES_COL, STATUS_COL, CROWN_COL])



if uploaded_file is not None:
    df = df.rename(columns={"CoorX": "X", "CoorY": "Y"})
    if len(plots) == 2:
            col1, col2 = st.columns(2)

            for i, plot_id in enumerate(plots):
                subset = df[df["PlotID"] == plot_id]
                colors = assign_colors(subset[SPECIES_COL].unique())

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
