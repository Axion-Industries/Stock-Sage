
import streamlit as st
import streamlit.components.v1 as components
from auth import init_auth, restore_session_from_storage
import json

# Configure page
st.set_page_config(
    page_title="Professional Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

# Handle session restoration from localStorage
if 'session_restored' not in st.session_state:
    st.session_state.session_restored = False

# JavaScript to handle session restoration
session_handler = """
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'restore_session') {
        // Session will be restored on next page load
        window.location.reload();
    }
});

// Check for saved session on page load
const savedSession = localStorage.getItem('stock_dashboard_session');
if (savedSession && !window.sessionRestored) {
    try {
        const sessionData = JSON.parse(savedSession);
        window.sessionRestored = true;
        // You would need to implement the actual session restoration here
        // For now, we'll redirect to Dashboard.py
        window.location.href = '/Dashboard.py';
    } catch (e) {
        localStorage.removeItem('stock_dashboard_session');
    }
}
</script>
"""

components.html(session_handler, height=0)

# Initialize auth
init_auth()

if not st.session_state.authenticated:
    st.markdown("# Welcome to Professional Stock Market Dashboard")
    st.markdown("Please navigate to the main dashboard to login.")
    
    if st.button("Go to Dashboard"):
        st.switch_page("Dashboard.py")
else:
    st.switch_page("Dashboard.py")
