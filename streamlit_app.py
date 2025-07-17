import streamlit as st
from tree_plots import load_data, process_data, plot_data, species_markers, species_colors
import pandas as pd 

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

df = pd.DataFrame(example_data)
st.set_page_config(page_title="Tree Plot Visualizer", layout="centered")
st.title("Tree Plot Visualizer")
st.write("Upload a CSV with tree data (species, DBH) to generate a plot.")

uploaded_file = st.file_uploader("Choose the data file (csv)", type="csv")

if uploaded_file is not None:
    try:
        data3, species_labels = load_data(uploaded_file)
        processed_data = process_data(data3, species_labels)
        plot_data(processed_data)

    except Exception as e:
        st.error(f"Error Processing file:{e}")


if st.checkbox("Troubleshooting:"):
    st.write("CSV must retain columns as below:")
    st.dataframe(df.set_index(df.columns[0]))