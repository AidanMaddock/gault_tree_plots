# GitHub Copilot / AI Agent Instructions for gault_tree_plots

Purpose
- Help AI coding agents become productive quickly in this repository (Streamlit app + analysis scripts).

Big picture (what the project is)
- This repo provides tools to visualize and analyse tree-plot data via a Streamlit app.
- UI pages live in `pages/` (Streamlit multipage). The root app entry is `streamlit_app.py`.
- Core data logic is in `tree_plots.py` (loading, normalization, plotting helpers) and `tree_statistics.py` (time-series and biodiversity metrics).

Key workflows (how developers run and test locally)
- Install dependencies: `pip install -r requirements.txt`.
- Run the app locally: `streamlit run streamlit_app.py` (use the dev container's Python if applicable).
- Example data: `example_data.csv` is a small working dataset used by UI "See an example".

Important project conventions and patterns
- Centralized config: constants and column-name aliases are defined in `config.py`. Prefer using those constants (e.g. `PLOTID_COL`, `DIAMETER_COL`, `PLOT_SIZE_METERS`) rather than hard-coding strings.
- Coordinate normalization: `normalize_coordinates()` in `tree_plots.py` is used early to ensure `X`/`Y` exist and are numeric. Many pages call it before plotting.
- PlotID vs PlotDisplay: the app supports two formats — an internal `PlotID` like `1-1` and a display form like `1 - 1`. Pages (for example `pages/Comparison.py`) convert between these when needed. Handle both formats when filtering datasets.
- Data column expectations: date/Year column present for time-series; species column name provided by `SPECIES_COL` in `config.py`; diameter column name by `DIAMETER_COL`.
- Avoid duplicating logic: use `load_data`, `assign_colors`, `plot_data` from `tree_plots.py` and stats functions from `tree_statistics.py`.

Integration points & external deps
- Streamlit UI (`streamlit`), Plotly (`plotly`), Matplotlib and Pandas are key libraries (see `requirements.txt`).
- Plots are created either with Matplotlib (some helpers) or Plotly `make_subplots` + `go` traces (see `pages/Comparison.py`).

How to modify UI pages
- Add pages under `pages/` — Streamlit will pick them up automatically.
- When adding plot controls, follow existing patterns: build selections in the sidebar, normalize coordinates, coerce `X`/`Y` to numeric and apply modulo `PLOT_SIZE_METERS`.

Files to inspect when changing behavior
- `tree_plots.py` — data loaders, coordinate handling, `plot_data()` and `assign_colors()`.
- `tree_statistics.py` — `compute_plot_year_stats()`, `diversity()`, `compute_dbh_increments()`.
- `config.py` — canonical column names and constants used across pages.
- `pages/Comparison.py` — a representative, non-trivial page showing multi-dataset comparisons and how control files are supported.

Examples of useful edits
- To add a new plot type: add a helper in `tree_plots.py` and call it from the page's `if subset is not None` block like `pages/Comparison.py`.
- To support a new column name: add it to `config.py` and update callers to reference the constant.

What not to change without caution
- `config.py` constants (column name aliases) — changing them affects all pages.
- Data-normalisation code in `tree_plots.py` — many pages assume normalized `X`/`Y` and `PlotID` formats.

If something is unclear
- Open `pages/Comparison.py` and `tree_plots.py` first — they hold the main control flow and data transformations.
- Ask the repo owner for expected CSV column names if sample data fails to load.

Ready for iteration
- I added this summary to `.github/copilot-instructions.md`. Tell me if you want more examples, unit-test guidance, or to merge existing instructions if you have an older copy to preserve.
