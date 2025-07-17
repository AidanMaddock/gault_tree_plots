import matplotlib.pyplot as plt
import streamlit as st
from tree_plots import assign_colors

DIAMETER_COL = "DBH"
SPECIES_COL = "Species"



def diversity_plot(species_counts, colourwheel):
    fig2, ax = plt.subplots(figsize=(4, 4))
    species_counts.plot(kind="pie", ax=ax, color=colourwheel)
    ax.set_title("Tree Species Diversity")
    ax.set_xlabel("Species")
    plt.xticks(rotation=45, ha='right')

    # Display in Streamlit
    st.pyplot(fig2)

def dbh_plot(df, selected_species,numbins, colourwheel, colourtype):

    colors = plt.cm.tab20.colors
    color_map = {sp: colors[i % len(colors)] for i, sp in enumerate(selected_species)}
    fig, ax = plt.subplots(figsize=(10, 6))
    for sp in selected_species:
        subset = df[df[SPECIES_COL] == sp][DIAMETER_COL].dropna()
        if colourtype:
            ax.hist(subset, bins=numbins, alpha=0.6, label=sp, color=colourwheel[sp])
            ax.legend(title="Species")
        else:
            ax.hist(subset, bins=numbins, alpha=0.6, label=sp, color="black")

    ax.set_title("DBH Distribution by Species")
    ax.set_xlabel("DBH (cm)")
    ax.set_ylabel("Number of Trees")
    
    st.pyplot(fig)
    
    
