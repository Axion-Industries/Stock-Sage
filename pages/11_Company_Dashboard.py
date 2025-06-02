
import streamlit as st
from auth import init_auth, require_auth, get_current_user

st.set_page_config(page_title="Feature Unavailable", page_icon="🚫", layout="wide")

# Initialize authentication
init_auth()

@require_auth
def main():
    user = get_current_user()
    
    st.title("🚫 Feature Unavailable")
    st.markdown("**The Company Dashboard feature has been removed.**")
    
    st.info("This section is no longer available. Please use other features of Stock Sage for your stock market analysis needs.")
    
    st.markdown("### Available Features:")
    st.markdown("""
    - **Dashboard**: Market overview and quick stats
    - **Market Overview**: Major indices and sector performance
    - **Stock Search**: Search and analyze individual stocks
    - **Stocks**: Manage your stock portfolio
    - **Watchlist**: Monitor stocks of interest
    - **Technical Analysis**: Advanced charting and indicators
    - **News**: Market news and analysis
    - **Inventory Management**: Product tracking
    - **Sales Analytics**: Sales reports and performance
    - **Barcode Scanner**: Product operations
    - **Settings**: Customize your experience
    """)

if __name__ == "__main__":
    main()
