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
perc_cols = [c for c in ta_df.columns if c.startswith("perc") and "ta" in c]

if len(perc_cols) == 0:
    st.error("❌ No percentile TA columns found")
    st.stop()

# extract percentile number
def get_perc(x):
    return int(re.findall(r'\d+', x)[0])

perc_cols = sorted(perc_cols, key=get_perc)
x_vals = [get_perc(c) for c in perc_cols]

# ================= SECTOR =================
def ci_to_sector(ci):
    if str(ci).endswith("1"):
        return "SEC1"
    elif str(ci).endswith("2"):
        return "SEC2"
    elif str(ci).endswith("3"):
        return "SEC3"
    return "UNK"

# ================= SITE SELECT =================
sites = sorted(mcom["site"].dropna().unique())
selected_site = st.selectbox("Select Site", sites)

st.markdown(f"### 📡 Site: {selected_site}")

# ================= FILTER =================
ci_list = mcom[mcom["site"] == selected_site]["ci"].unique()
df = ta_df[ta_df["ci"].isin(ci_list)]

# ================= JOIN =================
df = df.merge(mcom, on="ci", how="left")

# ================= BAND =================
df["band"] = df["band"].astype(str)

# ================= SECTOR =================
df["sector"] = df["ci"].apply(ci_to_sector)

# ================= PLOT =================
def plot_curve(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

    row = df_sec.iloc[0]

    y = row[perc_cols].values

    fig = go.Figure()

    fig.add_scatter(
        x=x_vals,
        y=y,
        mode="lines+markers",
        name="TA Percentile",
        line=dict(color="blue")
    )

    # TA90 marker
    if "perc90_ta" in row:
        ta90 = row["perc90_ta"]
        fig.add_scatter(
            x=[90],
            y=[ta90],
            mode="markers",
            marker=dict(color="red", size=10),
            name="TA 90%"
        )

    fig.update_layout(
        title=title,
        xaxis_title="Percentile (%)",
        yaxis_title="TA Distance (Km)",
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= LOOP =================
bands = sorted(df["band"].dropna().unique())
sectors = ["SEC1","SEC2","SEC3"]

for band in bands:

    st.markdown(f"## 📡 Band: L{band}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:

            df_sec = df[
                (df["band"] == band) &
                (df["sector"] == sec)
            ]

            plot_curve(df_sec, sec)
