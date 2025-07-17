import streamlit as st
from tree_plots import load_data, plot_data, assign_colors
from statistics_1 import diversity_plot, dbh_plot
import pandas as pd 
import numpy as np

DIAMETER_COL = "DBH"
SPECIES_COL = "Species"
OUTPUT_PATH = "output.png"

st.set_page_config(page_title="Tree Plot Visualizer", layout="centered")
st.title("Tree Plot Visualizer")
st.write("Upload a CSV with tree data (species, DBH) to generate a plot.")

# Upload File
uploaded_file = st.file_uploader("Choose the data file (csv)", type="csv")


if uploaded_file is not None:
    df = load_data(uploaded_file)
    df = df.rename(columns={"CoorX (m)": "X", "CoorY (m)": "Y", "DBH (cm)": "DBH"})
    if df is not None:
        try:

            
            colors = assign_colors(df[SPECIES_COL].unique())
            fn = plot_data(df, colors)

            species_counts = df["Species"].value_counts().sort_values(ascending=False)
            with st.sidebar:
                
                #Diversity Plots
                st.write("Graphs:")
                diversity_plot(species_counts, colors)
                st.write(f"Total Trees: {len(df)}")
                st.write(f"Unique Species: {len(species_counts)}")

                

                #DBH Selections
                species_list = sorted(df[SPECIES_COL].dropna().unique())
                species_options = ["Select All"] + species_list
                selected = st.multiselect("Choose species:", options=species_options, default=["Select All"])

                if "Select All" in selected:
                    selected_species = species_list
                else:
                    selected_species = selected

                filtered_df = df[df[SPECIES_COL].isin(selected_species)]
                
                num_bins = st.slider("Number of bins for DBH histogram", min_value=5, max_value=50, value=10)
                all_dbh = df[DIAMETER_COL].dropna()
                bin_edges = np.histogram_bin_edges(all_dbh, bins=num_bins)
                one_colour = st.checkbox("Use Species-Specific Colouring")
                dbh_plot(filtered_df, selected_species,bin_edges, colors, one_colour)
                if selected_species:
                    st.write(f"Average DBH: {filtered_df[DIAMETER_COL].mean():.2f} cm")



            #Bottom Columns   
            col1,col2,col3 = st.columns(3)
            with col1:
                st.write("Year: 2025")
            with col2:
                with open(fn, "rb") as img:
                        btn = st.download_button(
                            label="Download Graph",
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
example_data = {
    'Date': ['2025-07-15', '2025-07-15', '2025-07-15'],
    'Quadrat': [1, 2, 1],
    'TreeID': [101, 102, 201],
    'CoorX (m)': [10.5, 11.2, 12.8],
    'CoorY (m)': [20.3, 19.8, 22.1],
    'Species': ['QR', 'AS', 'OV'],
    'Status': ['AS', 'DS', 'AS'],
    'DBH (cm)': [30.2, 22.5, 18.7],
    'CrownClass': [3,2,1]
}


dfex = pd.DataFrame(example_data)
with st.expander("Troubleshooting"):
    st.write("CSV must contain columns in order as below:")
    st.dataframe(dfex.set_index(dfex.columns[0]))

