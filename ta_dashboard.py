import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide")
st.title("📊 NDO TA Dashboard (Real Histogram)")

# ================= LOAD =================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("TA_Chart_pmCounter - Copy.csv")
    except Exception as e:
        st.error(f"❌ Load CSV error: {e}")
        st.stop()

    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

# ================= VALIDATE =================
required_cols = ["eutrancellfdd", "distance", "pmtainit2distr"]
for c in required_cols:
    if c not in df.columns:
        st.error(f"❌ Missing column: {c}")
        st.stop()

# ================= PARSE DISTANCE =================
def parse_distance(x):
    nums = re.findall(r"[\d.]+", str(x))
    return float(nums[-1]) if nums else None

df["distance_km"] = df["distance"].apply(parse_distance)

# ================= SECTOR =================
def get_sector(cell):
    cell = str(cell)
    if cell.endswith("1"): return "SEC1"
    if cell.endswith("2"): return "SEC2"
    if cell.endswith("3"): return "SEC3"
    return "UNK"

df["sector"] = df["eutrancellfdd"].apply(get_sector)

# ================= BAND (AUTO DETECT) =================
# contoh: L1800, L2100, dll (sesuaikan kalau beda)
if "band" not in df.columns:
    # fallback: ambil dari nama cell (optional)
    df["band"] = "Unknown"

# ================= FILTER =================
col1, col2 = st.columns(2)

with col1:
    cells = sorted(df["eutrancellfdd"].dropna().unique())
    selected_site = st.selectbox("Select CELL", cells)

with col2:
    bands = ["All"] + sorted(df["band"].dropna().unique())
    selected_band = st.selectbox("Select BAND", bands)

df_f = df[df["eutrancellfdd"] == selected_site]

if selected_band != "All":
    df_f = df_f[df_f["band"] == selected_band]

if df_f.empty:
    st.warning("No Data")
    st.stop()

# ================= GROUP =================
df_g = (
    df_f.groupby(["sector", "distance_km"], as_index=False)["pmtainit2distr"]
    .sum()
    .sort_values("distance_km")
)

# ================= PLOT =================
def plot_chart(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

    sample = df_sec["pmtainit2distr"]
    x = df_sec["distance_km"]

    cum = sample.cumsum()
    cum_pct = cum / cum.max() * 100

    fig = go.Figure()

    # BAR
    fig.add_bar(
        x=x,
        y=sample,
        name="Sample",
        marker_color="#4C78A8"
    )

    # LINE
    fig.add_scatter(
        x=x,
        y=cum_pct,
        mode="lines+markers",
        name="% Cumulative",
        yaxis="y2",
        line=dict(color="green")
    )

    # BASELINE
    threshold = 90
    fig.add_hline(y=threshold, line_dash="dash", line_color="red")

    # TA90
    idx = cum_pct.ge(threshold).idxmax()

    fig.add_scatter(
        x=[x.loc[idx]],
        y=[cum_pct.loc[idx]],
        mode="markers",
        marker=dict(color="red", size=10, symbol="x"),
        name="TA 90%"
    )

    fig.update_layout(
        title=title,
        height=320,
        xaxis_title="Distance (Km)",
        yaxis_title="Sample",
        yaxis2=dict(
            overlaying="y",
            side="right",
            title="% Cumulative"
        ),
        legend=dict(orientation="h")
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= DASHBOARD =================
st.markdown("## 📡 Sector View")

cols = st.columns(3)
sectors = ["SEC1", "SEC2", "SEC3"]

for i, sec in enumerate(sectors):
    with cols[i]:

        df_sec = df_g[df_g["sector"] == sec]

        plot_chart(df_sec, sec)
