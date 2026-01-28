import streamlit as st
import sys, os
import pandas as pd 

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



dfex = pd.read_csv("Data/example_data.csv")

st.write("CSV must contain columns in order as below:")
st.dataframe(dfex.set_index(dfex.columns[0]))
st.write("Make sure that date is in format DD/MM/YYYY and that numeric values are not stored as text or include extra spaces.")