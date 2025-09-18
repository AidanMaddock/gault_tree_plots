import streamlit as st
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
st.set_page_config(page_title="Cross Section")

from tree_plots import load_data, plot_data, assign_colors
from interactive import plot_interactive, prepare_plot_data, plot_with_hover_line
from statistics_1 import diversity_plot, dbh_plot
import pandas as pd 
import numpy as np

DIAMETER_COL = "DBH"
SPECIES_COL = "Species"
OUTPUT_PATH = "output.png"
CROWN_COL = "CrownClass"
STATUS_COL = "Status"

st.set_page_config(page_title="Tree Plot Visualizer", layout="centered")
st.title("Tree Plot Visualizer")
st.write("Upload a CSV with tree data (species, DBH) to generate a plot. This page focuses on cross-sectional analysis, to compare tree distributions, select the 'Comparison' page in the upper left.")

# App to produce DBH histogram with species selection 
def dbh_app(df):
    species_list = sorted(df[SPECIES_COL].dropna().unique())
    species_options = ["Select All"] + species_list
    selected = st.multiselect("Choose species:", options=species_options, default=["Select All"])

    if "Select All" in selected:
        selected_species = species_list
    else:
        selected_species = selected

    filtered_df = df[df[SPECIES_COL].isin(selected_species)]
    
    num_bins = st.slider("Number of bins for DBH histogram", min_value=5, max_value=20, value=10)
    all_dbh = df[DIAMETER_COL].dropna()
    bin_edges = np.histogram_bin_edges(all_dbh, bins=num_bins)
    one_colour = st.checkbox("Use Species-Specific Colouring", value = True)
    dbh_plot(filtered_df, selected_species,bin_edges, colors, one_colour)
    if selected_species:
        st.write(f"Average DBH: {filtered_df[DIAMETER_COL].mean():.2f} cm")


# Upload File
uploaded_file = st.file_uploader("Choose the data file (csv)", type="csv")


if uploaded_file is not None:
    df = load_data(uploaded_file)
    df = df.rename(columns={"CoorX": "X", "CoorY": "Y", "DBH)": "DBH"})
    if df is not None:
        try:
            colors = assign_colors(df[SPECIES_COL].unique())
            topcol1, topcol2,topcol3 = st.columns([2,1,2])
            with topcol1:
                plotting_group = st.selectbox("Pick attribute to plot trees by", [SPECIES_COL, STATUS_COL, CROWN_COL])
            if "Year" in df.columns:  
                year_list = df["Year"].dropna().unique()
                with topcol2:
                    year = st.pills("Pick Year to Plot Data",year_list, default = year_list[0])
            with topcol3:
                interactive = st.checkbox("Interactive Chart")
            if interactive:
                plot_interactive(df,year)    
            else:
                fn = plot_data(df, colors, plotting_group,year)
                

            species_counts = df["Species"].value_counts().sort_values(ascending=False)
            with st.sidebar:
                
                #Diversity Plots
                st.write("Graphs:")
                diversity_plot(species_counts, colors)
                st.metric("Total trees:", len(df))
                st.metric("Unique Species", len(species_counts))

                #DBH Plot and Selection
                dbh_app(df)
                
            #Bottom Columns   
            col1,col2,col3 = st.columns(3)
            with col1:
                st.write("Year: 2025")
            with col2:
                if not interactive:
                    with open(fn, "rb") as img:
                            btn = st.download_button(
                                label="Download Figure",
                                data=img,
                                file_name=fn,
                                on_click = "ignore",
                                mime="image/png"
                            )
            with col3:
                st.write("Created by Aidan Maddock")



        except Exception as e:
            st.error(f"Error during plotting: {e}. Refer to the troubleshooting section")
    else:
        st.warning("Data could not be loaded. Check integrity of file")



# Troubleshooting Info
dfex = pd.read_csv("example_data.csv")
with st.expander("Troubleshooting"):
    st.write("CSV must contain columns in order as below:")
    st.dataframe(dfex.set_index(dfex.columns[0]))
    st.write("Make sure that date is in format DD/MM/YYYY and that numeric values are not stored as text or include extra spaces.")

##DBH Graphing Functions
