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

    # 🔥 CLEAN COLUMN NAME
    ta.columns = (
        ta.columns
        .str.lower()
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    mcom.columns = mcom.columns.str.lower()

    ta["ci"] = ta["ci"].astype(str)
    mcom["ci"] = mcom["ci"].astype(str)

    return ta, mcom

try:
    ta_df, mcom = load_data()
except Exception as e:
    st.error("Load error")
    st.text(str(e))
    st.stop()

# ================= VALIDATION =================
if ta_df.empty or mcom.empty:
    st.error("Data kosong")
    st.stop()

# ================= DETECT PERCENTILE =================
perc_cols = [c for c in ta_df.columns if c.startswith("perc")]

if len(perc_cols) == 0:
    st.error("Kolom perc tidak ditemukan")
    st.write(ta_df.columns)
    st.stop()

def get_perc(x):
    try:
        return int(re.findall(r'\d+', x)[0])
    except:
        return 0

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
    st.error("Kolom site tidak ada")
    st.stop()

sites = sorted(mcom["site"].dropna().unique())
selected_site = st.selectbox("Select Site", sites)

st.write("Selected:", selected_site)

# ================= FILTER =================
ci_list = mcom[mcom["site"] == selected_site]["ci"].unique()

df = ta_df[ta_df["ci"].isin(ci_list)]

if df.empty:
    st.warning("No TA data")
    st.stop()

# ================= MERGE =================
df = df.merge(mcom, on="ci", how="left")

# ================= BAND FIX =================
band_col = None
for c in ["band_y", "band", "lte_band"]:
    if c in df.columns:
        band_col = c
        break

if band_col is None:
    st.error("Band column not found")
    st.write(df.columns)
    st.stop()

df["band_clean"] = df[band_col].astype(str)

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
        mode="lines+markers"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Percentile",
        yaxis_title="TA (Km)",
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= LOOP =================
bands = sorted(df["band_clean"].dropna().unique())
sectors = ["SEC1","SEC2","SEC3"]

for band in bands:

    st.markdown(f"## Band L{band}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:
            df_sec = df[
                (df["band_clean"] == band) &
                (df["sector"] == sec)
            ]
            plot_curve(df_sec, sec)
