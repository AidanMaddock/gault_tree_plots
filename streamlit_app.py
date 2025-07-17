import streamlit as st
from tree_plots import load_data, process_data, plot_data, assign_colors
import pandas as pd 

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
            plot_data(df, colors)
        except Exception as e:
            st.error(f"Error during plotting: {e}. Refer to the troubleshooting section")
    else:
        st.warning("Data could not be loaded.")




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
if st.checkbox("Troubleshooting:"):
    st.write("CSV must contain columns in order as below:")
    st.dataframe(dfex.set_index(dfex.columns[0]))