import streamlit as st

st.set_page_config(page_title="Page Not Found", page_icon="🚫", layout="wide")

st.title("🚫 Page Not Available")
st.markdown("**This page has been removed from Stock Sage.**")

st.info("The Company Dashboard feature is no longer available. Please use the main dashboard and other features.")

st.markdown("### 🏠 [Go to Main Dashboard](/Dashboard.py)")
st.markdown("### 📈 [View Market Overview](/pages/01_Market_Overview.py)")
st.markdown("### 💼 [Manage Your Stocks](/pages/03_Portfolio.py)")