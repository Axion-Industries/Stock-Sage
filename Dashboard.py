import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.data_fetcher import DataFetcher
from utils.portfolio_manager import PortfolioManager
from utils.stock_symbols import StockSymbolFetcher
from auth import init_auth, login_page, get_current_user, logout
import streamlit.components.v1 as components

# Configure page
st.set_page_config(
    page_title="Professional Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS and JavaScript
def load_custom_assets():
    with open('static/css/style.css', 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

    with open('static/js/effects.js', 'r') as f:
        js = f.read()
    components.html(f'<script>{js}</script>', height=0)

load_custom_assets()

# Initialize authentication first
init_auth()

# Check authentication
if not st.session_state.authenticated:
    login_page()
    st.stop()

# Initialize components after authentication
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = DataFetcher()

if 'portfolio_manager' not in st.session_state:
    st.session_state.portfolio_manager = PortfolioManager()

if 'stock_symbols' not in st.session_state:
    st.session_state.stock_symbols = StockSymbolFetcher()

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Apply dark theme by default
import streamlit.components.v1 as components
components.html("""
<script>
// Apply dark theme by default
document.body.style.backgroundColor = '#0f172a';
document.body.style.color = '#f8fafc';

// Apply dark theme to Streamlit elements
const style = document.createElement('style');
style.textContent = `
    .stApp {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }
    .stSidebar {
        background-color: #1e293b !important;
    }
    .stSelectbox label, .stTextInput label, .stDateInput label {
        color: #f8fafc !important;
    }
`;
document.head.appendChild(style);
</script>
""", height=0)

# Main page content
user = get_current_user()
st.title("📈 Stock Sage - Professional Dashboard")
if user:
    st.markdown(f"Welcome back, **{user['username']}**! Your comprehensive stock market analysis platform")
else:
    st.markdown("Welcome to your comprehensive stock market analysis platform")

# Quick stats section
col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        spy_data = yf.Ticker("SPY").history(period="1d")
        if not spy_data.empty:
            spy_price = spy_data['Close'].iloc[-1]
            spy_change = spy_data['Close'].iloc[-1] - spy_data['Open'].iloc[-1]
            spy_pct_change = (spy_change / spy_data['Open'].iloc[-1]) * 100

            st.metric(
                label="S&P 500 (SPY)",
                value=f"${spy_price:.2f}",
                delta=f"{spy_pct_change:.2f}%"
            )
        else:
            st.metric("S&P 500 (SPY)", "N/A", "Data unavailable")
    except Exception as e:
        st.metric("S&P 500 (SPY)", "Error", f"Failed to fetch data")

with col2:
    try:
        nasdaq_data = yf.Ticker("QQQ").history(period="1d")
        if not nasdaq_data.empty:
            nasdaq_price = nasdaq_data['Close'].iloc[-1]
            nasdaq_change = nasdaq_data['Close'].iloc[-1] - nasdaq_data['Open'].iloc[-1]
            nasdaq_pct_change = (nasdaq_change / nasdaq_data['Open'].iloc[-1]) * 100

            st.metric(
                label="NASDAQ (QQQ)",
                value=f"${nasdaq_price:.2f}",
                delta=f"{nasdaq_pct_change:.2f}%"
            )
        else:
            st.metric("NASDAQ (QQQ)", "N/A", "Data unavailable")
    except Exception as e:
        st.metric("NASDAQ (QQQ)", "Error", f"Failed to fetch data")

with col3:
    try:
        dow_data = yf.Ticker("DIA").history(period="1d")
        if not dow_data.empty:
            dow_price = dow_data['Close'].iloc[-1]
            dow_change = dow_data['Close'].iloc[-1] - dow_data['Open'].iloc[-1]
            dow_pct_change = (dow_change / dow_data['Open'].iloc[-1]) * 100

            st.metric(
                label="DOW (DIA)",
                value=f"${dow_price:.2f}",
                delta=f"{dow_pct_change:.2f}%"
            )
        else:
            st.metric("DOW (DIA)", "N/A", "Data unavailable")
    except Exception as e:
        st.metric("DOW (DIA)", "Error", f"Failed to fetch data")

with col4:
    try:
        vix_data = yf.Ticker("^VIX").history(period="1d")
        if not vix_data.empty:
            vix_price = vix_data['Close'].iloc[-1]
            vix_change = vix_data['Close'].iloc[-1] - vix_data['Open'].iloc[-1]

            st.metric(
                label="VIX",
                value=f"{vix_price:.2f}",
                delta=f"{vix_change:.2f}"
            )
        else:
            st.metric("VIX", "N/A", "Data unavailable")
    except Exception as e:
        st.metric("VIX", "Error", f"Failed to fetch data")

# Quick stock lookup
st.subheader("Quick Stock Lookup")
col1, col2 = st.columns([3, 1])

with col1:
    symbol = st.text_input("Enter stock symbol (e.g., AAPL, GOOGL, MSFT):", placeholder="AAPL")

with col2:
    if st.button("Search", type="primary"):
        if symbol:
            try:
                ticker = yf.Ticker(symbol.upper())
                info = ticker.info
                hist = ticker.history(period="1d")

                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[-1]
                    change = current_price - open_price
                    pct_change = (change / open_price) * 100

                    st.success(f"**{symbol.upper()}**: ${current_price:.2f} ({pct_change:+.2f}%)")

                    # Additional info if available
                    if 'longName' in info:
                        st.write(f"**Company**: {info['longName']}")
                    if 'marketCap' in info and info['marketCap']:
                        market_cap = info['marketCap'] / 1e9
                        st.write(f"**Market Cap**: ${market_cap:.2f}B")
                else:
                    st.error(f"No data found for symbol: {symbol.upper()}")
            except Exception as e:
                st.error(f"Error fetching data for {symbol.upper()}: {str(e)}")

# Recent activity section
st.subheader("Market Activity")

# Top gainers and losers (using popular stocks as example)
popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA']

try:
    stock_data = []
    for stock in popular_stocks:
        try:
            ticker = yf.Ticker(stock)
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                change = current_price - open_price
                pct_change = (change / open_price) * 100

                stock_data.append({
                    'Symbol': stock,
                    'Price': current_price,
                    'Change': change,
                    'Change %': pct_change
                })
        except:
            continue

    if stock_data:
        df = pd.DataFrame(stock_data)
        df = df.sort_values('Change %', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Top Gainers**")
            top_gainers = df.head(4)
            for _, row in top_gainers.iterrows():
                st.metric(
                    label=row['Symbol'],
                    value=f"${row['Price']:.2f}",
                    delta=f"{row['Change %']:.2f}%"
                )

        with col2:
            st.write("**Top Losers**")
            top_losers = df.tail(4)
            for _, row in top_losers.iterrows():
                st.metric(
                    label=row['Symbol'],
                    value=f"${row['Price']:.2f}",
                    delta=f"{row['Change %']:.2f}%"
                )
    else:
        st.warning("Unable to fetch market activity data at this time.")

except Exception as e:
    st.error(f"Error loading market activity: {str(e)}")

# Removed theme settings - dark theme is permanent

# Navigation info
st.sidebar.markdown("## 🚀 Navigation")
st.sidebar.markdown("""
**Stock Market Analysis:**
- **Dashboard**: Overview and market data  
- **Market Overview**: Major indices and sector performance
- **Stock Search**: Search and analyze individual stocks  
- **Stocks**: Track your holdings and performance
- **Watchlist**: Monitor stocks of interest
- **Technical Analysis**: Advanced charting and indicators
- **News**: Market news and analysis

**Business Management:**
- **Inventory Management**: Product tracking and operations
- **Sales Analytics**: Sales reports and performance analysis
- **Barcode Scanner**: Quick product operations and scanning
- **Settings**: Customize your experience and preferences
""")

# User Account
st.sidebar.markdown("## 👤 Account")
if user:
    st.sidebar.write(f"**User:** {user['username']}")
    if st.sidebar.button("Logout", type="secondary"):
        logout()

# Auto-refresh option
if st.sidebar.toggle("Auto-refresh (5 min)"):
    import time
    time.sleep(300)
    st.rerun()