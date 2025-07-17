import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import io
import streamlit as st 
from collections import defaultdict
import itertools
import pandas as pd

# Plotting Constants


DIAMETER_COL = "DBH"
SPECIES_COL = "Species"
OUTPUT_PATH = "output.png"


def load_data(filelike):
    if filelike is not None:
        try:
            df = pd.read_csv(filelike)
            st.success("File successfully uploaded and read.")
            return df
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None

    return None

def assign_colors(species_list):
    known_species_colors = {
    "QR": "green",
    "TC": "blue",
    "AP": "orange",
    "PR": "purple",
    "FG": "brown",
    "AS": "red",
    "OV": "olive",
    "AR": "lightpink",
    "AA": "peru",
    "FA": "black"}  
    color_cycle = itertools.cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])
    used = set(known_species_colors.values())
    color_cycle = (c for c in color_cycle if c not in used)
    return defaultdict(lambda: next(color_cycle), known_species_colors)

def process_data(data,species):
    data4 = [(*point, label) for point, label in zip(data, species)] 
    x_coords = [x for x, y, dbh, sp in data4]
    y_coords = [y for x, y, dbh, sp in data4]
    dbh_list = [dbh * 3 for x, y, dbh, sp in data4]
    species_list = [sp for x, y, dbh, sp in data4]
    return (x_coords,y_coords,dbh_list,species_list)

def plot_data(df, species_colors):
    fig, ax = plt.subplots(figsize=(8, 7))
    for sp, group in df.groupby(SPECIES_COL):
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
    ax.set_title('Tree Plot by Species, Scaled by DBH')

    dbh_sizes = [5, 15, 30, 45]  
    marker_sizes = [dbh * 3 for dbh in dbh_sizes]
    dbh_handles = [
        plt.scatter([], [], s=size, color='gray', label=f"{dbh} cm", alpha=0.6)
        for dbh, size in zip(dbh_sizes, marker_sizes)
    ]

    ax.legend(title="Species", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)


