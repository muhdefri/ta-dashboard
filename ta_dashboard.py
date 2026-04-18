import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

st.set_page_config(layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}

.card {
    background-color: #ffffff;
    padding: 10px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    margin-bottom: 15px;
}

.no-data {
    background-color: #f5f5dc;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    color: #666;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("# 📊 NDO TA & MDT DASHBOARD")
st.markdown("### TA 4G CELL")

# ================= LOAD =================
@st.cache_data
def load_data():
    ta = pd.read_csv("ta_stat_20260409.csv")
    mcom = pd.read_csv("mcom.csv")

    ta.columns = ta.columns.str.lower()
    mcom.columns = mcom.columns.str.lower()

    ta["ci"] = ta["ci"].astype(str)
    mcom["ci"] = mcom["ci"].astype(str)

    return ta, mcom

ta_df, mcom_df = load_data()

# ================= FILTER =================
c1, c2, c3 = st.columns(3)

with c1:
    site = st.selectbox("Select SITE", sorted(mcom_df["site_id"].unique()))

with c2:
    band = st.selectbox("Select BAND", ["All"] + sorted(mcom_df["band"].unique()))

with c3:
    baseline = st.slider("Baseline (%)", 80, 100, 90)

# ================= JOIN =================
site_df = mcom_df[mcom_df["site_id"] == site]

if band != "All":
    site_df = site_df[site_df["band"] == band]

df = ta_df[ta_df["ci"].isin(site_df["ci"])]
df = df.merge(site_df, on="ci", how="left")

# ================= SECTOR =================
def get_sector(ci):
    if ci.endswith("1"): return "SEC1"
    if ci.endswith("2"): return "SEC2"
    if ci.endswith("3"): return "SEC3"
    return "UNK"

df["sector"] = df["ci"].apply(get_sector)

# ================= HIST =================
def build_hist(row):
    cols = [c for c in row.index if "_ta_distance_km" in c]

    def num(x):
        return int(re.findall(r'\d+', x)[0])

    cols = sorted(cols, key=num)

    x = [num(c) for c in cols]
    y = pd.to_numeric(row[cols], errors="coerce").values
    hist = np.diff(np.insert(y, 0, 0))

    return x, hist, y

# ================= CHART =================
def plot_chart(df_sec, title):

    if df_sec.empty:
        st.markdown('<div class="no-data">No Data</div>', unsafe_allow_html=True)
        return

    row = df_sec.iloc[0]
    x, hist, cum = build_hist(row)

    fig = go.Figure()

    fig.add_bar(x=x, y=hist, name="Sample", marker_color="#4C78A8")

    fig.add_scatter(
        x=x, y=cum,
        mode="lines+markers",
        name="% Cumulative",
        yaxis="y2",
        line=dict(color="green")
    )

    threshold = baseline / 100 * max(cum)

    fig.add_hline(y=threshold, line_dash="dash", line_color="red")

    idx = np.argmax(cum >= threshold)

    fig.add_scatter(
        x=[x[idx]],
        y=[cum[idx]],
        mode="markers",
        marker=dict(color="red", size=10, symbol="x"),
        name="Baseline"
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=12)),
        height=260,
        margin=dict(l=5, r=5, t=30, b=5),
        xaxis_title="Range (Km)",
        yaxis_title="Sample",
        yaxis2=dict(overlaying="y", side="right"),
        legend=dict(orientation="h", y=-0.3)
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= DASHBOARD =================
bands = sorted(df["band"].dropna().unique())

for b in bands:

    st.markdown(f"## 📶 Band: L{int(b)}")

    col1, col2, col3 = st.columns(3)

    sectors = ["SEC1", "SEC2", "SEC3"]

    for i, sec in enumerate(sectors):

        with [col1, col2, col3][i]:

            st.markdown('<div class="card">', unsafe_allow_html=True)

            df_sec = df[(df["band"] == b) & (df["sector"] == sec)]

            title = sec
            if not df_sec.empty:
                title = df_sec.iloc[0]["cell_name"]

            plot_chart(df_sec, title)

            st.markdown('</div>', unsafe_allow_html=True)
