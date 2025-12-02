import plotly.express as px
import streamlit as st 
import plotly.graph_objects as go


#This file interactively plots data

DIAMETER_COL = "DBH"
SPECIES_COL = "Species"
OUTPUT_PATH = "output.png"
STATUS_COL = "Status"
CROWN_COL = "CrownClass"

def get_dbh_history(df, tree_id):
    tree_data = df[df["TreeID"] == tree_id].sort_values("Year")
    return list(tree_data["DBH"]), list(tree_data["Year"])

def prepare_plot_data(df, year):
    df = df.copy()
    # ensure coordinate columns are named 'X' and 'Y'
    if 'CoorX' in df.columns and 'X' not in df.columns:
        df.rename(columns={'CoorX': 'X', 'CoorY': 'Y'}, inplace=True)
    df['TreeID'] = df['X'].astype(str) + "_" + df['Y'].astype(str)

    df_year = df[df['Year'] == year]

    # Attach tree history
    history = df.groupby("TreeID").apply(lambda group: group.sort_values("Year")[["Year", "DBH"]].values.tolist())
    history = history.to_dict()

    df_year["customdata"] = df_year["TreeID"].map(history)
    return df_year

def plot_with_hover_line(df_year):
    fig = go.Figure()

    for _, row in df_year.iterrows():
        years_dbh = row["customdata"]
        if not years_dbh:
            continue
        years, dbhs = zip(*years_dbh)

        fig.add_trace(go.Scatter(
            x=[row["X"]],
            y=[row["Y"]],
            mode='markers',
            marker=dict(size=row["DBH"] * 3, color='blue', opacity=0.7),
            hovertemplate=
            f'<b>TreeID: {row["TreeID"]}</b><br>' +
            'X: %{x}, Y: %{y}<br>' +
            'DBH: %{marker.size:.1f}<br><br>' +
            'DBH over Years:<br>' +
            ''.join(f'{y}: {d:.1f} cm<br>' for y, d in zip(years, dbhs)) +
            '<extra></extra>'
        ))

    fig.update_layout(
        title="Hover over a tree to see its DBH history",
        xaxis=dict(range=[0, 20], title="Meters (x)"),
        yaxis=dict(range=[0, 20], title="Meters (y)"),
        width=800,
        height=700
    )

    st.plotly_chart(fig)


def plot_interactive(df, year):
    df = df.copy()
    # ensure coordinate columns are named 'X' and 'Y' so plotting works regardless of column naming in the uploaded CSV
    if 'CoorX' in df.columns and 'X' not in df.columns:
        df.rename(columns={'CoorX': 'X', 'CoorY': 'Y'}, inplace=True)

    df_year = df[df['Year'] == year]
    if df_year.empty:
        st.warning(f"No data found for year {year}.")
        return

    df_year['DBH_size'] = df_year[DIAMETER_COL]
    fig = px.scatter(
        df_year,
        x='X',
        y='Y',
        color=SPECIES_COL,
        size='DBH_size',
        hover_data=[SPECIES_COL, DIAMETER_COL, STATUS_COL, CROWN_COL, 'Date'],
        title=f"Interactive Tree Plot for {year}",
        labels={'X': 'Meters (x)', 'Y': 'Meters (y)'},
        width=800,
        height=700
    )

    fig.update_traces(marker=dict(opacity=0.8), selector=dict(mode='markers'))
    fig.update_layout(yaxis_range=[0, 20], xaxis_range=[0, 20])
    st.plotly_chart(fig, use_container_width=True)
