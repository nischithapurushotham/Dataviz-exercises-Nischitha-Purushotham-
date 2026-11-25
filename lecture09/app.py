# ── Lecture 9 Class Exercise: Step 4 dashboard + diverging colour chart ──────

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Page configuration, title and data source
st.set_page_config(page_title="World Happiness Report", page_icon="🌐", layout="wide")
st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

# Data ingestion
# Path is built relative to this file so it works both locally and on Streamlit Cloud.
# Adjust if your CSV lives somewhere else in your repo.
DATA_PATH = Path(__file__).parent.parent / "data" / "world_happiness_2023.csv"


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df.columns = ["Country", "Region", "Score", "GDP", "Social_Support",
                  "Life_Expectancy", "Freedom", "Generosity", "Corruption"]
    return df


df = load_data(DATA_PATH)
global_avg = df["Score"].mean()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    regions = ["All Regions"] + sorted(df["Region"].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N", 5, 25, 15)

# Filter data by region and top_n
filtered = df if selected_region == "All Regions" else df[df["Region"] == selected_region]
top = filtered.nlargest(top_n, "Score").sort_values("Score")

# KPI row
col1, col2, col3 = st.columns(3)
col1.metric("Countries", len(filtered))
col2.metric("Avg Score", f"{filtered['Score'].mean():.2f}",
            f"{filtered['Score'].mean() - global_avg:+.2f} vs global")
col3.metric("Happiest", filtered.nlargest(1, "Score")["Country"].values[0])

st.divider()

left, right = st.columns(2)

# ── Chart 1: top N bar chart (from Step 4) ───────────────────────────────────
fig = px.bar(top, x="Score", y="Country", orientation="h",
             labels={"Score": "Happiness Score (0–10)", "Country": ""},
             template="plotly_white",
             title=f"Happiest {top_n} Countries in 2023 - {selected_region}")
fig.update_layout(title_font=dict(family="Arial", size=13, color="slategrey"),
                  xaxis=dict(range=[0, 8.0]), height=600)
left.plotly_chart(fig, width="stretch")

# ── Chart 2 (exercise): diverging colour scale around the global average ─────
# Meaningful midpoint = global average happiness score.
# Positive deviation = happier than the world average (blue),
# negative deviation = less happy (red).
if selected_region == "All Regions":
    dev = df.groupby("Region", as_index=False)["Score"].mean()
    label_col = "Region"
    chart2_title = "Regional average happiness vs global average"
else:
    dev = filtered[["Country", "Score"]].copy()
    label_col = "Country"
    chart2_title = f"{selected_region}: each country vs global average"

dev["Deviation"] = dev["Score"] - global_avg
dev = dev.sort_values("Deviation")

# Symmetric colour range so 0 sits exactly in the neutral middle of the scale
lim = dev["Deviation"].abs().max()

fig2 = px.bar(dev, x="Deviation", y=label_col, orientation="h",
              color="Deviation",
              color_continuous_scale="RdBu",
              color_continuous_midpoint=0,
              range_color=[-lim, lim],
              hover_data={"Score": ":.2f", "Deviation": ":+.2f"},
              labels={"Deviation": "Difference from global average", label_col: ""},
              template="plotly_white", title=chart2_title)

# Midpoint line + annotation
fig2.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="dimgrey")
fig2.add_annotation(x=0, y=1.0, xref="x", yref="paper",
                    yanchor="bottom", xanchor="center", showarrow=False,
                    text=f"<b>Midpoint: global average = {global_avg:.2f}</b>",
                    font=dict(family="Arial", size=11, color="dimgrey"),
                    bgcolor="white")

fig2.update_layout(title_font=dict(family="Arial", size=13, color="slategrey"),
                   xaxis=dict(range=[-lim * 1.1, lim * 1.1]),
                   coloraxis_colorbar=dict(title="Δ vs global"),
                   margin=dict(t=80),
                   height=600)
right.plotly_chart(fig2, width="stretch")

st.divider()
st.caption("Built with Streamlit + Plotly")
