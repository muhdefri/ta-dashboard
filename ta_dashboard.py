import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

st.set_page_config(layout="wide")

# ================= HEADER =================
st.markdown("""
# 📊 NDO TA & MDT DASHBOARD
### TA 4G CELL
""")

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
col1, col2, col3 = st.columns(3)

with col1:
    site_list = sorted(mcom_df["site_id"].dropna().unique())
    selected_site = st.selectbox("Select SITE", site_list)

with col2:
    band_list = ["All"] + sorted(mcom_df["band"].dropna().astype(int).unique().tolist())
    selected_band = st.selectbox("Select BAND", band_list)

with col3:
    baseline = st.slider("Baseline (%)", 80, 100, 90)

# ================= JOIN =================
site_mcom = mcom_df[mcom_df["site_id"] == selected_site]

if selected_band != "All":
    site_mcom = site_mcom[site_mcom["band"] == selected_band]

ci_list = site_mcom["ci"].unique()

df = ta_df[ta_df["ci"].isin(ci_list)]
df = df.merge(site_mcom, on="ci", how="left")

# ================= SECTOR =================
def get_sector(ci):
    if ci.endswith("1"): return "SEC1"
    if ci.endswith("2"): return "SEC2"
    if ci.endswith("3"): return "SEC3"
    return "UNK"

df["sector"] = df["ci"].apply(get_sector)

# ================= HIST =================
def build_hist(row):

    perc_cols = [c for c in row.index if "_ta_distance_km" in c]

    def get_num(x):
        return int(re.findall(r'\d+', x)[0])

    perc_cols = sorted(perc_cols, key=get_num)

    x = [get_num(c) for c in perc_cols]
    y = pd.to_numeric(row[perc_cols], errors="coerce").values

    hist = np.diff(np.insert(y, 0, 0))

    return x, hist, y

# ================= PLOT =================
def plot_chart(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

    row = df_sec.iloc[0]
    x, hist, cum = build_hist(row)

    fig = go.Figure()

    # BAR
    fig.add_bar(
        x=x,
        y=hist,
        name="Sample",
        marker_color="#4C78A8"
    )

    # LINE
    fig.add_scatter(
        x=x,
        y=cum,
        mode="lines+markers",
        name="% Cumulative",
        yaxis="y2",
        line=dict(color="green")
    )

    # BASELINE
    threshold = baseline / 100 * max(cum)

    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color="red"
    )

    # MARKER X
    idx = np.argmax(cum >= threshold)

    fig.add_scatter(
        x=[x[idx]],
        y=[cum[idx]],
        mode="markers",
        marker=dict(color="red", size=10, symbol="x"),
        name="Baseline"
    )

    fig.update_layout(
        title=title,
        height=280,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Range (Km)",
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
bands = sorted(df["band"].dropna().unique())

for band in bands:

    st.markdown(f"## 📶 Band: L{int(band)}")

    cols = st.columns(3)

    sectors = ["SEC1", "SEC2", "SEC3"]

    for i, sec in enumerate(sectors):

        with cols[i]:

            df_sec = df[
                (df["band"] == band) &
                (df["sector"] == sec)
            ]

            title = sec

            if not df_sec.empty:
                title = df_sec.iloc[0]["cell_name"]

            plot_chart(df_sec, title)
