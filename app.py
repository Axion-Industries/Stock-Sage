import streamlit as st
import streamlit.components.v1 as components

# Configure page
st.set_page_config(
    page_title="Stock Sage - Landing",
    page_icon="📈",
    layout="wide"
)

# Redirect to landing page HTML
components.html("""
<script>
window.location.href = '/index.html';
</script>
""", height=0)

st.markdown("# Welcome to Stock Sage")
st.markdown("Redirecting to landing page...")