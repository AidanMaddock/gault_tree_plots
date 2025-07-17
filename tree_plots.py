import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import io
import streamlit as st 
from collections import defaultdict
import itertools

# Plotting Constants
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
    "FA": "black"
}

species_markers = defaultdict(lambda: "o")
color_cycle = itertools.cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])
used_colors = set(known_species_colors.values())
color_cycle = (c for c in color_cycle if c not in used_colors)

species_colors = defaultdict(lambda: next(color_cycle), known_species_colors)


def load_data(filelike):
    data3 = []
    species_labels = []

    text = io.StringIO(filelike.read().decode("utf-8"))
    
    next(text)
    for row in text: 
        data = row.strip().split(",")
        if data[3] and data[4] and data[7]:
            data3.append((float(data[3]),float(data[4]),float(data[7])))
        species_labels.append(str(data[5]).strip())

    return data3,species_labels

def process_data(data,species):
    data4 = [(*point, label) for point, label in zip(data, species)] 
    x_coords = [x for x, y, dbh, sp in data4]
    y_coords = [y for x, y, dbh, sp in data4]
    dbh_list = [dbh * 3 for x, y, dbh, sp in data4]
    species_list = [sp for x, y, dbh, sp in data4]
    return (x_coords,y_coords,dbh_list,species_list)

def plot_data(processed_data):
    x_coords, y_coords, dbh_list, species_list = processed_data
    fig, ax = plt.subplots(figsize=(7, 7))
    for sp in set(species_list):
        xs = [x for x, s in zip(x_coords, species_list) if s == sp]
        ys = [y for y, s in zip(y_coords, species_list) if s == sp]
        sizes = [dbh for dbh, s in zip(dbh_list, species_list) if s == sp]
        ax.scatter(xs, ys,
                c=species_colors.get(sp, "grey"),
                marker=species_markers.get(sp, "o"),
                s=sizes,
                label=sp,
                edgecolors='black', linewidth=0.5)


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


    scale_handles = [
        plt.scatter([], [], s=size, c='gray', edgecolors='black', label=f"{dbh} cm")
        for size, dbh in zip(marker_sizes, dbh_sizes)
    ]
    ax.legend(title="Species", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)


#load_data("/Users/aidanmaddock/Downloads/2025_Bioplot_Data(5 Hemlock Knoll).csv")
#processed_data = process_data(data3, species_labels)
#plot_data(processed_data)