import streamlit as st
import sys, os
import pandas as pd 
from config import TROUBLESHOOTING_TEXT

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



dfex = pd.read_csv("Data/example_data.csv")
dfdi = pd.read_csv("Data/TreeDict.csv")
dfst = pd.read_csv("Data/StatusDict.csv")

col1, col2, col3 = st.columns([1,0.2,1])

with col1:
    st.header("Example Data Format")
    st.write("CSV must contain columns in order as below:")
    st.dataframe(dfex.set_index(dfex.columns[0]), height = 200)
    st.write(TROUBLESHOOTING_TEXT)

with col3: 
    st.header("Species Codes")
    st.dataframe(dfdi.set_index(dfdi.columns[0]), height = 200)

    st.header("Status Codes")
    st.dataframe(dfst.set_index(dfst.columns[0]), height = 200)
    