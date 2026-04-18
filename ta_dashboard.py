import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import re

st.set_page_config(layout="wide")
st.title("📊 TA Dashboard (NDO Style)")

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

# ================= FILTER SITE =================
site_list = sorted(mcom_df["site_id"].dropna().unique())
selected_site = st.selectbox("Select Site ID", site_list)

site_mcom = mcom_df[mcom_df["site_id"] == selected_site]
ci_list = site_mcom["ci"].unique()

df = ta_df[ta_df["ci"].isin(ci_list)]
df = df.merge(site_mcom, on="ci", how="left")

# ================= SECTOR =================
def ci_to_sector(ci):
    ci = str(ci)
    if ci.endswith("1"): return "SEC1"
    if ci.endswith("2"): return "SEC2"
    if ci.endswith("3"): return "SEC3"
    return "UNK"

df["sector"] = df["ci"].apply(ci_to_sector)

# ================= HISTOGRAM SIMULATION =================
def build_histogram(row):

    perc_cols = [c for c in row.index if "_ta_distance_km" in c]

    def get_perc(x):
        return int(re.findall(r'\d+', x)[0])

    perc_cols = sorted(perc_cols, key=get_perc)

    x = [get_perc(c) for c in perc_cols]
    y = pd.to_numeric(row[perc_cols], errors="coerce").values

    # simulate histogram dari percentile
    hist = np.diff(np.insert(y, 0, 0))

    return x, hist, y

# ================= PLOT =================
def plot_ta(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

    row = df_sec.iloc[0]

    x, hist, cum = build_histogram(row)

    fig = go.Figure()

    # 🔵 BAR (Sample)
    fig.add_bar(
        x=x,
        y=hist,
        name="Sample"
    )

    # 🟢 CUMULATIVE
    fig.add_scatter(
        x=x,
        y=cum,
        mode="lines+markers",
        name="% Cumulative",
        yaxis="y2"
    )

    # 🔴 90% LINE
    fig.add_hline(
        y=0.9 * max(cum),
        line_dash="dash",
        line_color="red"
    )

    # ❌ MARKER X
    idx_90 = np.argmax(cum >= 0.9 * max(cum))
    fig.add_scatter(
        x=[x[idx_90]],
        y=[cum[idx_90]],
        mode="markers",
        marker=dict(color="red", size=10, symbol="x"),
        name="90%"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Range (Km)",
        yaxis=dict(title="Sample"),
        yaxis2=dict(
            title="% Cumulative",
            overlaying="y",
            side="right"
        ),
        height=300,
        legend=dict(orientation="h")
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= LOOP =================
bands = sorted(df["band"].dropna().unique())
sectors = ["SEC1","SEC2","SEC3"]

for band in bands:

    st.markdown(f"## 📡 Band L{int(band)}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:

            df_sec = df[
                (df["band"] == band) &
                (df["sector"] == sec)
            ]

            plot_ta(df_sec, sec)
