import matplotlib.pyplot as plt
import plotly.express as px
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import io
import streamlit as st 
from collections import defaultdict
import itertools
import pandas as pd
from tree_objects import get_dbh_history
import time

# Plotting Constants

#Make importing CSV strip header names and turn to lowercase
DIAMETER_COL = "DBH"
SPECIES_COL = "Species"
OUTPUT_PATH = "output.png"
STATUS_COL = "Status "
CROWN_COL = "CrownClass"


def load_data(filelike):
    if filelike is not None:
        try:
            
            df = pd.read_csv(filelike)

            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=False)
                df['Year'] = df['Date'].dt.year
            else:
                st.warning("No 'Date' column found. Year-based filtering will not be available.")

            alert = st.success("File successfully uploaded and read.")
            
            return df
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None

    return None


# Assign colours for known species for parity between plot generation and choose from colourwheel if not in list
def assign_colors(species_list):
    known_species_colors = {
    "QR": "green", "TC": "blue", "AP": "orange", "PR": "purple", "FG": "brown", "AS": "red", "OV": "olive", "AR": "lightpink", "AA": "peru", "FA": "black"}  
    color_cycle = itertools.cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])
    used = set(known_species_colors.values())
    color_cycle = (c for c in color_cycle if c not in used)
    return defaultdict(lambda: next(color_cycle), known_species_colors)

def plot_data(df, species_colors, plotting_group,year):
    fig, ax = plt.subplots(figsize=(8, 7))
    df = df[df["Year"] == year]
    for sp, group in df.groupby(plotting_group):
        ax.scatter(group["X"], group["Y"], s=group[DIAMETER_COL] * 3, 
                   c=species_colors[sp], label=sp, marker='o', alpha = 0.8)
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.axvline(x=10, color='red', linestyle='-', linewidth=1)
    ax.axhline(y=10, color='red', linestyle='-', linewidth=1)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 20)
    ax.set_xticks(range(0, 21, 1))
    ax.set_yticks(range(0, 21, 1))
    ax.set_xlabel('Meters (x)')
    ax.set_ylabel('Meters (y)')
    ax.set_title(f'Tree Plot by {plotting_group}, {year}, Scaled by DBH')

    dbh_sizes = [5, 15, 30, 45]  
    marker_sizes = [dbh * 3 for dbh in dbh_sizes]
    dbh_handles = [
        plt.scatter([], [], s=size, color='gray', label=f"{dbh} cm", alpha=0.6)
        for dbh, size in zip(dbh_sizes, marker_sizes)
    ]

    ax.legend(title=plotting_group, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)
    fn = 'tree_plot.png'

    # Prepare figure for download
    plt.savefig(fn)
    return fn



