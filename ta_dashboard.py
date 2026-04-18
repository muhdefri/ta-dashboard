import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide")
st.title("📊 TA Dashboard (Site Based)")

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    ta = pd.read_csv("ta_stat_20260409.csv")
    mcom = pd.read_csv("mcom.csv")

    # normalize column
    ta.columns = ta.columns.str.lower()
    mcom.columns = mcom.columns.str.lower()

    # ensure ci string
    ta["ci"] = ta["ci"].astype(str)
    mcom["ci"] = mcom["ci"].astype(str)

    return ta, mcom

try:
    ta_df, mcom = load_data()
except Exception as e:
    st.error("❌ Gagal load data")
    st.text(str(e))
    st.stop()

# ================= VALIDATION =================
if ta_df.empty:
    st.error("❌ TA data kosong")
    st.stop()

if mcom.empty:
    st.error("❌ MCOM data kosong")
    st.stop()

# ================= DETECT PERCENTILE =================
perc_cols = [c for c in ta_df.columns if "perc" in c and "ta" in c]

if len(perc_cols) == 0:
    st.error("❌ Kolom percentile TA tidak ditemukan")
    st.stop()

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

# ================= SITE =================
if "site" not in mcom.columns:
    st.error("❌ Kolom 'site' tidak ada di MCOM")
    st.stop()

sites = sorted(mcom["site"].dropna().unique())

if len(sites) == 0:
    st.error("❌ Tidak ada site di MCOM")
    st.stop()

selected_site = st.selectbox("Select Site", sites)

st.markdown(f"### 📡 Site: {selected_site}")

# ================= FILTER =================
ci_list = mcom[mcom["site"] == selected_site]["ci"].unique()

df = ta_df[ta_df["ci"].isin(ci_list)]

if df.empty:
    st.warning("⚠️ Tidak ada data TA untuk site ini")
    st.stop()

# ================= MERGE =================
df = df.merge(mcom, on="ci", how="left")

# ================= FIX BAND =================
if "band_y" in df.columns:
    df["band_clean"] = df["band_y"].astype(str)
elif "band" in df.columns:
    df["band_clean"] = df["band"].astype(str)
else:
    st.error("❌ Kolom band tidak ditemukan")
    st.stop()

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
        name="TA Curve"
    )

    # TA90 marker
    if "perc90_ta" in df_sec.columns:
        ta90 = row.get("perc90_ta", None)
        if pd.notna(ta90):
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
bands = sorted(df["band_clean"].dropna().unique())
sectors = ["SEC1","SEC2","SEC3"]

for band in bands:

    st.markdown(f"## 📡 Band: L{band}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:

            df_sec = df[
                (df["band_clean"] == band) &
                (df["sector"] == sec)
            ]

            plot_curve(df_sec, sec)
