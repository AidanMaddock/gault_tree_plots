import matplotlib.pyplot as plt
import streamlit as st

def diversity_plot(species_counts):
    fig2, ax = plt.subplots(figsize=(4, 4))
    species_counts.plot(kind="pie", ax=ax, color="skyblue")
    ax.set_title("Tree Species Diversity")
    ax.set_xlabel("Species")
    ax.set_ylabel("Number of Trees")
    plt.xticks(rotation=45, ha='right')

    # Display in Streamlit
    st.pyplot(fig2)
