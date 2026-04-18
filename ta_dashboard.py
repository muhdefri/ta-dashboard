import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re

st.set_page_config(layout="wide")
st.title("📊 TA Dashboard (Site Based)")

# ================= DEBUG =================
st.subheader("🔍 Debug Files")
st.write("Files:", os.listdir())

# ================= LOAD =================
@st.cache_data
def load_data():
    try:
        ta = pd.read_csv("ta_stat_20260409.csv")
        st.success("✅ TA loaded")
    except Exception as e:
        st.error(f"❌ TA ERROR: {e}")
        st.stop()

    try:
        mcom = pd.read_csv("mcom.csv")
        st.success("✅ MCOM loaded")
    except Exception as e:
        st.error(f"❌ MCOM ERROR: {e}")
        st.stop()

    ta.columns = ta.columns.str.lower()
    mcom.columns = mcom.columns.str.lower()

    ta["ci"] = ta["ci"].astype(str)
    mcom["ci"] = mcom["ci"].astype(str)

    return ta, mcom

ta_df, mcom_df = load_data()

# ================= VALIDATION =================
if "ci" not in ta_df.columns:
    st.error("❌ Missing CI in TA")
    st.stop()

for col in ["site_id", "ci", "band"]:
    if col not in mcom_df.columns:
        st.error(f"❌ Missing {col} in MCOM")
        st.stop()

st.success("✅ Column OK")

# ================= DETECT TA =================
perc_cols = [c for c in ta_df.columns if "_ta_distance_km" in c]

if len(perc_cols) == 0:
    st.error("❌ No TA percentile column found")
    st.stop()

def get_perc(x):
    return int(re.findall(r'\d+', x)[0])

perc_cols = sorted(perc_cols, key=get_perc)
x_vals = [get_perc(c) for c in perc_cols]

# ================= SELECT SITE =================
site_list = sorted(mcom_df["site_id"].dropna().unique())
selected_site = st.selectbox("Select Site ID", site_list)

# ================= FILTER =================
site_mcom = mcom_df[mcom_df["site_id"] == selected_site]

if site_mcom.empty:
    st.warning("No MCOM data")
    st.stop()

ci_list = site_mcom["ci"].unique()
df = ta_df[ta_df["ci"].isin(ci_list)]

if df.empty:
    st.warning("No TA data")
    st.stop()

# ================= MERGE =================
df = df.merge(site_mcom, on="ci", how="left")
st.success("✅ Data Ready")

# ================= SECTOR =================
def ci_to_sector(ci):
    ci = str(ci)
    if ci.endswith("1"): return "SEC1"
    if ci.endswith("2"): return "SEC2"
    if ci.endswith("3"): return "SEC3"
    return "UNK"

df["sector"] = df["ci"].apply(ci_to_sector)

# ================= PLOT =================
def plot_curve(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

    row = df_sec.iloc[0]

    # convert to numpy biar aman
    y = pd.to_numeric(row[perc_cols], errors="coerce").values

    x = []
    y_clean = []

    for i in range(len(y)):
        if pd.notna(y[i]):
            x.append(x_vals[i])
            y_clean.append(y[i])

    if len(y_clean) == 0:
        st.warning("No valid data")
        return

    fig = go.Figure()

    fig.add_scatter(
        x=x,
        y=y_clean,
        mode="lines+markers",
        name="TA Curve"
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
sectors = ["SEC1", "SEC2", "SEC3"]

for band in bands:

    st.markdown(f"## 📡 Band L{int(band)}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:

            df_sec = df[
                (df["band"] == band) &
                (df["sector"] == sec)
            ]

            plot_curve(df_sec, sec)
