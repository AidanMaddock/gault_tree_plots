import streamlit as st

# Main page with navigation set in Streamlit
pg = st.navigation([st.Page("Cross_Section.py"), st.Page("Comparison.py")],position="top"
)
pg.run()

