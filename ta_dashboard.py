import streamlit as st
import pandas as pd
import os

st.title("DEBUG MODE")

st.write("FILES:", os.listdir())

try:
    ta = pd.read_csv("ta_stat_20260409.csv")
    st.success("TA loaded")
    st.write(ta.head())

    mcom = pd.read_csv("mcom.csv")
    st.success("MCOM loaded")
    st.write(mcom.head())

except Exception as e:
    st.error("ERROR TERJADI")
    st.text(str(e))
