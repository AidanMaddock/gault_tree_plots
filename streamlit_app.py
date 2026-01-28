import streamlit as st

# Main page with navigation set in Streamlit
pg = st.navigation([st.Page("pages/Comparison.py"), st.Page("pages/Troubleshooting.py")],position="top"
)
pg.run()

