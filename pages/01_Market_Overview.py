import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from utils.data_fetcher import DataFetcher

st.set_page_config(page_title="Market Overview", page_icon="📊", layout="wide")

# Initialize data fetcher
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = DataFetcher()

data_fetcher = st.session_state.data_fetcher

st.title("📊 Market Overview")

# Get market indices data
indices_data = data_fetcher.get_market_indices()

if indices_data:
    # Display major indices
    st.subheader("Major Market Indices")
    
    cols = st.columns(len(indices_data))
    for i, (name, data) in enumerate(indices_data.items()):
        with cols[i]:
            delta_color = "normal"
            if data['percent_change'] > 0:
                delta_color = "normal"  # Green
            elif data['percent_change'] < 0:
                delta_color = "inverse"  # Red
            
            st.metric(
                label=name,
                value=f"{data['price']:.2f}",
                delta=f"{data['percent_change']:.2f}%"
            )

    # Market performance chart
    st.subheader("Market Performance Today")
    
    # Create performance comparison chart
    fig = go.Figure()
    
    for name, data in indices_data.items():
        if 'data' in data and not data['data'].empty:
            hist_data = data['data']
            # Normalize to percentage change from open
            if len(hist_data) > 0:
                open_price = hist_data['Open'].iloc[0]
                if open_price > 0:  # Avoid division by zero
                    pct_change = ((hist_data['Close'] - open_price) / open_price) * 100
                    
                    fig.add_trace(
                        go.Scatter(
                            x=hist_data.index,
                            y=pct_change,
                            mode='lines',
                            name=name,
                            line=dict(width=2)
                        )
                    )
    
    fig.update_layout(
        title="Intraday Performance (% Change from Open)",
        xaxis_title="Time",
        yaxis_title="Percentage Change (%)",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Sector performance
st.subheader("Sector Performance")

sector_etfs = {
    'Technology': 'XLK',
    'Healthcare': 'XLV',
    'Financials': 'XLF',
    'Energy': 'XLE',
    'Consumer Discretionary': 'XLY',
    'Utilities': 'XLU',
    'Real Estate': 'XLRE',
    'Materials': 'XLB',
    'Industrials': 'XLI',
    'Consumer Staples': 'XLP',
    'Communication': 'XLC'
}

try:
    sector_data = []
    for sector, etf in sector_etfs.items():
        try:
            ticker = yf.Ticker(etf)
            data = ticker.history(period="1d")
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                open_price = data['Open'].iloc[-1]
                change = current_price - open_price
                pct_change = (change / open_price) * 100
                
                sector_data.append({
                    'Sector': sector,
                    'ETF': etf,
                    'Price': current_price,
                    'Change %': pct_change
                })
        except:
            continue
    
    if sector_data:
        sector_df = pd.DataFrame(sector_data)
        sector_df = sector_df.sort_values('Change %', ascending=False)
        
        # Create sector performance chart
        fig = go.Figure(data=[
            go.Bar(
                x=sector_df['Sector'],
                y=sector_df['Change %'],
                marker_color=['green' if x >= 0 else 'red' for x in sector_df['Change %']],
                text=[f"{x:.2f}%" for x in sector_df['Change %']],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Sector Performance Today",
            xaxis_title="Sector",
            yaxis_title="Change (%)",
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display sector data in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top Performing Sectors**")
            top_sectors = sector_df.head(5)
            for _, row in top_sectors.iterrows():
                st.metric(
                    label=f"{row['Sector']} ({row['ETF']})",
                    value=f"${row['Price']:.2f}",
                    delta=f"{row['Change %']:.2f}%"
                )
        
        with col2:
            st.write("**Worst Performing Sectors**")
            worst_sectors = sector_df.tail(5)
            for _, row in worst_sectors.iterrows():
                st.metric(
                    label=f"{row['Sector']} ({row['ETF']})",
                    value=f"${row['Price']:.2f}",
                    delta=f"{row['Change %']:.2f}%"
                )
    else:
        st.warning("Unable to fetch sector performance data at this time.")

except Exception as e:
    st.error(f"Error loading sector data: {str(e)}")

# Market movers
st.subheader("Market Movers")

# Popular stocks to track for movers
popular_stocks = [
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA',
    'AMD', 'INTC', 'CRM', 'ORCL', 'PYPL', 'SHOP', 'UBER', 'ZOOM',
    'JPM', 'BAC', 'V', 'MA', 'JNJ', 'PFE', 'KO', 'PEP', 'WMT', 'HD'
]

try:
    movers_data = []
    for symbol in popular_stocks:
        try:
            quote = data_fetcher.get_real_time_quote(symbol)
            if quote:
                movers_data.append({
                    'Symbol': symbol,
                    'Price': quote['price'],
                    'Change': quote['change'],
                    'Change %': quote['percent_change'],
                    'Volume': quote['volume']
                })
        except:
            continue
    
    if movers_data:
        movers_df = pd.DataFrame(movers_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top Gainers**")
            top_gainers = movers_df.nlargest(10, 'Change %')
            for _, row in top_gainers.iterrows():
                st.metric(
                    label=row['Symbol'],
                    value=f"${row['Price']:.2f}",
                    delta=f"{row['Change %']:.2f}%"
                )
        
        with col2:
            st.write("**Top Losers**")
            top_losers = movers_df.nsmallest(10, 'Change %')
            for _, row in top_losers.iterrows():
                st.metric(
                    label=row['Symbol'],
                    value=f"${row['Price']:.2f}",
                    delta=f"{row['Change %']:.2f}%"
                )
    else:
        st.warning("Unable to fetch market movers data at this time.")

except Exception as e:
    st.error(f"Error loading market movers: {str(e)}")

# Market statistics
st.subheader("Market Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Market Open", "9:30 AM EST")
    st.metric("Market Close", "4:00 PM EST")

with col2:
    # Calculate market status
    now = datetime.now()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if market_open <= now <= market_close and now.weekday() < 5:
        st.metric("Market Status", "OPEN", "🟢")
    else:
        st.metric("Market Status", "CLOSED", "🔴")

with col3:
    st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))

# Auto-refresh option
with st.sidebar:
    st.subheader("Settings")
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds")
    
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()
    
    if st.button("Refresh Data"):
        st.rerun()

# Market news placeholder
st.subheader("Market News")
st.info("📰 Market news integration would require a news API service. Current focus is on real-time market data display.")
