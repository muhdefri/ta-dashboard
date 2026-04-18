import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

st.title("📊 TA Dashboard (Site Based)")

# ================= DEBUG FILE CHECK =================
st.subheader("🔍 Debug Files")

files = os.listdir()
st.write("Files in repo:", files)

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    try:
        ta = pd.read_csv("ta_stat_20260409.csv")
        st.success("✅ TA file loaded")
        st.write("TA shape:", ta.shape)
        st.write(ta.head())
    except Exception as e:
        st.error(f"❌ TA ERROR: {e}")
        st.stop()

    try:
        mcom = pd.read_csv("mcom.csv")
        st.success("✅ MCOM file loaded")
        st.write("MCOM shape:", mcom.shape)
        st.write(mcom.head())
    except Exception as e:
        st.error(f"❌ MCOM ERROR: {e}")
        st.stop()

    return ta, mcom


ta_df, mcom_df = load_data()

# ================= CLEAN COLUMN =================
ta_df.columns = ta_df.columns.str.lower()
mcom_df.columns = mcom_df.columns.str.lower()

# ================= VALIDATION =================
required_ta = ["ci", "site"]
required_mcom = ["site_id", "ci", "band"]

for col in required_ta:
    if col not in ta_df.columns:
        st.error(f"❌ Missing column in TA: {col}")
        st.stop()

for col in required_mcom:
    if col not in mcom_df.columns:
        st.error(f"❌ Missing column in MCOM: {col}")
        st.stop()

st.success("✅ Column validation OK")

# ================= FILTER SITE =================
site_list = sorted(mcom_df["site_id"].dropna().unique())

selected_site = st.selectbox("Select Site ID", site_list)

site_mcom = mcom_df[mcom_df["site_id"] == selected_site]

if site_mcom.empty:
    st.warning("No MCOM data for this site")
    st.stop()

st.write("Selected site data:", site_mcom)

# ================= JOIN TA =================
merged = pd.merge(
    ta_df,
    site_mcom,
    on="ci",
    how="inner"
)

if merged.empty:
    st.warning("❌ No matching TA data after join")
    st.stop()

st.success("✅ Data joined")

# ================= DETECT PERCENTILE =================
perc_cols = [c for c in merged.columns if "perc" in c or "ta" in c]

if len(perc_cols) == 0:
    st.error("❌ No percentile columns found")
    st.stop()

st.write("Detected columns:", perc_cols)

# ================= GROUP BY BAND =================
bands = sorted(merged["band"].dropna().unique())

for band in bands:
    st.subheader(f"📡 Band L{int(band)}")

    band_df = merged[merged["band"] == band]

    if band_df.empty:
        st.warning("No data for this band")
        continue

    cols = st.columns(3)

    for i, (_, row) in enumerate(band_df.iterrows()):
        with cols[i % 3]:

            st.markdown(f"**CI {row['ci']}**")

            try:
                chart_data = row[perc_cols]

                st.line_chart(chart_data)

            except Exception as e:
                st.error(f"Chart error: {e}")
