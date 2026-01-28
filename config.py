"""Configuration constants for tree plot application."""

# Column names
DIAMETER_COL = "DBH"
SPECIES_COL = "Species"
STATUS_COL = "Status"
CROWN_COL = "CrownClass"
PLOTID_COL = "PlotID"
TREEID_COL = "StandardID"
YEAR_COL = "Year"
DATE_COL = "Date"
X_COL = "X"
Y_COL = "Y"

# Coordinate column aliases (for backward compatibility with uploaded data)
COORD_X_ALIASES = ["CoorX", "X", "Easting"]
COORD_Y_ALIASES = ["CoorY", "Y", "Northing"]

# Output paths
OUTPUT_PATH = "output.png"

# Plot dimensions
PLOT_SIZE_METERS = 20
PLOT_AREA_M2 = PLOT_SIZE_METERS ** 2
PLOT_CENTER = PLOT_SIZE_METERS / 2

# Marker scaling
DBH_MARKER_SCALE = 3
LEGEND_DBH_SIZES = [5, 15, 30, 45]

# Figure dimensions
MATPLOTLIB_FIGSIZE_WIDE = (10, 6)
MATPLOTLIB_FIGSIZE_SQUARE = (8, 7)
PLOTLY_WIDTH_WIDE = 800
PLOTLY_HEIGHT_WIDE = 700
PLOTLY_WIDTH_COMPARISON = 800
PLOTLY_HEIGHT_COMPARISON = 1000

# Species color mapping (known species)
KNOWN_SPECIES_COLORS = {
    "QR": "green",
    "TC": "blue",
    "AP": "orange",
    "PR": "purple",
    "FG": "brown",
    "AS": "red",
    "OV": "olive",
    "AR": "lightpink",
    "AA": "peru",
    "FA": "black",
}

# UI text
WELCOME_TEXT = "Upload a CSV with tree data (species, DBH) to generate a plot. Select plots to compare tree distributions and statistics over time."
DEFAULT_YEAR_TEXT_FORMAT = "Year: {}"
TROUBLESHOOTING_TEXT = "Make sure that date is in format DD/MM/YYYY and that numeric values are not stored as text or include extra spaces." \
" Plot / Subplot columns are optional. For acceptable aliases for columns, check config.py in the repo"

# Default settings
DEFAULT_BINS = 10
MIN_BINS = 5
MAX_BINS = 20
DEFAULT_MARKER_OPACITY = 0.8
DEFAULT_GRID_STYLE = "--"
DEFAULT_GRID_WIDTH = 0.5

# Statistical constants
MIN_SAMPLES_FOR_STATS = 2
