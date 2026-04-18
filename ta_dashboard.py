import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide")
st.title("📊 TA Dashboard (Site Based)")

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

ta_df, mcom = load_data()

# ================= DETECT PERCENTILE =================
perc_cols = [c for c in ta_df.columns if "ta_distance" in c]

def get_perc(x):
    return int(re.findall(r'\d+', x)[0])

perc_cols = sorted(perc_cols, key=get_perc)
x_vals = [get_perc(c) for c in perc_cols]

# ================= SITE =================
sites = sorted(mcom["site"].dropna().unique())
selected_site = st.selectbox("Select Site", sites)

# ================= FILTER =================
ci_list = mcom[mcom["site"] == selected_site]["ci"].unique()
df = ta_df[ta_df["ci"].isin(ci_list)]

if df.empty:
    st.warning("No TA data")
    st.stop()

# ================= MERGE =================
df = df.merge(mcom, on="ci", how="left")

# ================= BAND =================
df["band_clean"] = df["band"].astype(str)

# ================= SECTOR =================
def ci_to_sector(ci):
    if str(ci).endswith("1"): return "SEC1"
    if str(ci).endswith("2"): return "SEC2"
    if str(ci).endswith("3"): return "SEC3"
    return "UNK"

df["sector"] = df["ci"].apply(ci_to_sector)

# ================= PLOT =================
def plot_curve(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

    row = df_sec.iloc[0]

    # 🔥 CLEAN DATA NUMERIC
    y = pd.to_numeric(row[perc_cols], errors="coerce")
    
    # drop nan
    valid = ~y.isna()
    x = [x_vals[i] for i in range(len(x_vals)) if valid[i]]
    y = y[valid]

    if len(y) == 0:
        st.warning("No valid TA data")
        return

    fig = go.Figure()

    fig.add_scatter(
        x=x,
        y=y,
        mode="lines+markers"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Percentile",
        yaxis_title="TA Distance (Km)",
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= LOOP =================
bands = sorted(df["band_clean"].dropna().unique())
sectors = ["SEC1","SEC2","SEC3"]

for band in bands:

    st.markdown(f"## 📡 Band L{band}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:

            df_sec = df[
                (df["band_clean"] == band) &
                (df["sector"] == sec)
            ]

            plot_curve(df_sec, sec)
