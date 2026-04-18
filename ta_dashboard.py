import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide")
st.title("📊 TA Dashboard (CI Based)")

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    ta = pd.read_csv("ta_stat_20260409.csv")
    mcom = pd.read_csv("mcom.csv")

    ta["ci"] = ta["ci"].astype(str).str.strip()
    mcom["ci"] = mcom["ci"].astype(str).str.strip()

    return ta, mcom


ta_df, mcom = load_data()

# ================= EXTRACT TA BUCKET =================
ta_cols = [c for c in ta_df.columns if c.startswith("ta")]

def extract_km(col):
    if "gt" in col:
        return 7  # fallback max
    match = re.search(r'_(\d+)', col)
    if match:
        return int(match.group(1)) / 1000
    return 0

x_vals = [extract_km(c) for c in ta_cols]


# ================= CI TO SECTOR =================
def ci_to_sector(ci):
    ci = str(ci)
    if ci.endswith("1"):
        return "SEC1"
    elif ci.endswith("2"):
        return "SEC2"
    elif ci.endswith("3"):
        return "SEC3"
    return "UNK"


# ================= PLOT FUNCTION =================
def plot_ta_chart(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

    # ambil 1 row (1 cell)
    row = df_sec.iloc[0]

    y = row[ta_cols].values
    total = y.sum()

    if total == 0:
        st.warning("No TA sample")
        return

    cum = y.cumsum()
    cum_pct = cum / total * 100

    ta90 = row.get("perc90_ta_distance_km", None)

    fig = go.Figure()

    # histogram
    fig.add_bar(
        x=x_vals,
        y=y,
        name="Sample",
        marker_color="steelblue"
    )

    # cumulative
    fig.add_scatter(
        x=x_vals,
        y=cum_pct,
        name="% Cumulative",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="green")
    )

    # baseline 90%
    fig.add_hline(
        y=90,
        line_dash="dash",
        line_color="red"
    )

    # marker X
    if pd.notna(ta90):
        fig.add_scatter(
            x=[ta90],
            y=[90],
            mode="markers",
            marker=dict(color="red", size=10, symbol="x"),
            name="90%"
        )

    fig.update_layout(
        title=title,
        xaxis_title="Range (Km)",
        yaxis_title="Sample",
        yaxis2=dict(
            title="% Cumulative",
            overlaying="y",
            side="right",
            range=[0,110]
        ),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)


# ================= UI =================
selected_ci = st.multiselect(
    "Select CI",
    sorted(ta_df["ci"].unique())
)

if not selected_ci:
    st.stop()

# ================= FILTER =================
df = ta_df[ta_df["ci"].isin(selected_ci)]

# ================= JOIN MCOM =================
df = df.merge(mcom, on="ci", how="left")

# ================= BAND CLEAN =================
df["Band"] = (
    df["band"]
    .astype(str)
    .str.extract(r'(\d+)')
)

# ================= SECTOR =================
df["SECTOR_GROUP"] = df["ci"].apply(ci_to_sector)

# ================= LOOP BAND =================
bands = sorted(df["Band"].dropna().unique())
sectors = ["SEC1","SEC2","SEC3"]

for band in bands:

    st.markdown(f"## 📡 Band: L{band}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:

            df_sec = df[
                (df["Band"] == band) &
                (df["SECTOR_GROUP"] == sec)
            ]

            plot_ta_chart(df_sec, f"{sec}")
