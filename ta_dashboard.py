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

    # normalize column names
    ta.columns = ta.columns.str.lower()
    mcom.columns = mcom.columns.str.lower()

    # ensure key columns exist
    if "ci" not in ta.columns:
        st.error("❌ 'ci' column not found in TA file")
        st.stop()

    if "ci" not in mcom.columns:
        st.error("❌ 'ci' column not found in MCOM file")
        st.stop()

    # normalize values
    ta["ci"] = ta["ci"].astype(str).str.strip()
    mcom["ci"] = mcom["ci"].astype(str).str.strip()

    # detect site column
    site_col = None
    for col in ["site", "site_id", "enodeb"]:
        if col in mcom.columns:
            site_col = col
            break

    if site_col is None:
        st.error("❌ No site column found in MCOM (site/site_id/enodeb)")
        st.stop()

    # detect band column
    band_col = None
    for col in ["band", "lte_band", "freq"]:
        if col in mcom.columns:
            band_col = col
            break

    if band_col is None:
        st.error("❌ No band column found in MCOM")
        st.stop()

    return ta, mcom, site_col, band_col


ta_df, mcom, site_col, band_col = load_data()

# ================= TA BUCKET =================
ta_cols = [c for c in ta_df.columns if c.startswith("ta")]

if len(ta_cols) == 0:
    st.error("❌ No TA bucket columns found (ta0_xxx, ta1_xxx, etc)")
    st.stop()

def extract_km(col):
    if "gt" in col:
        return 7
    match = re.search(r'_(\d+)', col)
    if match:
        return int(match.group(1)) / 1000
    return 0

x_vals = [extract_km(c) for c in ta_cols]

# ================= SECTOR =================
def ci_to_sector(ci):
    ci = str(ci)
    if ci.endswith("1"):
        return "SEC1"
    elif ci.endswith("2"):
        return "SEC2"
    elif ci.endswith("3"):
        return "SEC3"
    return "UNK"

# ================= UI =================
sites = sorted(mcom[site_col].dropna().unique())

selected_site = st.selectbox("Select Site", sites)

st.markdown(f"### 📡 Site: {selected_site}")

# ================= FILTER =================
ci_list = mcom[mcom[site_col] == selected_site]["ci"].unique()

df = ta_df[ta_df["ci"].isin(ci_list)]

# ================= JOIN =================
df = df.merge(mcom, on="ci", how="left")

# ================= BAND =================
df["band_clean"] = (
    df[band_col]
    .astype(str)
    .str.extract(r'(\d{3,4})')
)

df["band_clean"] = df["band_clean"].replace({
    "1850": "1800",
    "1840": "1800"
})

# ================= SECTOR =================
df["sector"] = df["ci"].apply(ci_to_sector)

# ================= PLOT =================
def plot_ta_chart(df_sec, title):

    if df_sec.empty:
        st.warning("No Data")
        return

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

    fig.add_bar(x=x_vals, y=y, name="Sample")

    fig.add_scatter(
        x=x_vals,
        y=cum_pct,
        yaxis="y2",
        mode="lines+markers",
        name="% Cumulative",
        line=dict(color="green")
    )

    fig.add_hline(y=90, line_dash="dash", line_color="red")

    if pd.notna(ta90):
        fig.add_scatter(
            x=[ta90],
            y=[90],
            mode="markers",
            marker=dict(color="red", size=10, symbol="x"),
            name="TA 90%"
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
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= LOOP =================
bands = sorted(df["band_clean"].dropna().unique())
sectors = ["SEC1","SEC2","SEC3"]

if len(bands) == 0:
    st.warning("No Band Data Found")
    st.stop()

for band in bands:

    st.markdown(f"## 📡 Band: L{band}")

    cols = st.columns(3)

    for i, sec in enumerate(sectors):
        with cols[i]:

            df_sec = df[
                (df["band_clean"] == band) &
                (df["sector"] == sec)
            ]

            plot_ta_chart(df_sec, sec)
