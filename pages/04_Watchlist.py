import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils.data_fetcher import DataFetcher

st.set_page_config(page_title="Watchlist", page_icon="👁️", layout="wide")

from auth import init_auth, get_current_user, require_auth
from utils.data_persistence import data_persistence

# Initialize authentication
init_auth()

# Initialize data fetcher
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = DataFetcher()

# Load user's watchlist from database
user = get_current_user()
if user and 'watchlist' not in st.session_state:
    st.session_state.watchlist = data_persistence.get_user_watchlist(user['id'])
elif 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = {}

data_fetcher = st.session_state.data_fetcher

st.title("👁️ Watchlist & Alerts")

# Add stock to watchlist
st.subheader("Add Stock to Watchlist")

col1, col2 = st.columns([3, 1])

with col1:
    new_symbol = st.text_input("Enter stock symbol", placeholder="AAPL").upper()

with col2:
    st.write("")  # Spacer
    if st.button("Add to Watchlist", type="primary"):
        if new_symbol:
            if data_fetcher.validate_symbol(new_symbol):
                if new_symbol not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_symbol)
                    # Save to database if user is logged in
                    if user:
                        data_persistence.save_watchlist_item(user['id'], new_symbol)
                    st.success(f"Added {new_symbol} to watchlist!")
                else:
                    st.warning(f"{new_symbol} is already in your watchlist.")
            else:
                st.error(f"Invalid stock symbol: {new_symbol}")
        else:
            st.error("Please enter a stock symbol")

# Display watchlist
if st.session_state.watchlist:
    st.subheader("Your Watchlist")
    
    # Get real-time data for all watchlist stocks
    watchlist_data = []
    
    for symbol in st.session_state.watchlist:
        try:
            quote = data_fetcher.get_real_time_quote(symbol)
            if quote:
                # Check for price alerts
                alert_triggered = False
                alert_message = ""
                
                if symbol in st.session_state.price_alerts:
                    alerts = st.session_state.price_alerts[symbol]
                    for alert in alerts:
                        if alert['type'] == 'above' and quote['price'] >= alert['price']:
                            alert_triggered = True
                            alert_message = f"🔴 ALERT: {symbol} is above ${alert['price']:.2f}"
                        elif alert['type'] == 'below' and quote['price'] <= alert['price']:
                            alert_triggered = True
                            alert_message = f"🔴 ALERT: {symbol} is below ${alert['price']:.2f}"
                
                watchlist_data.append({
                    'Symbol': symbol,
                    'Price': quote['price'],
                    'Change': quote['change'],
                    'Change %': quote['percent_change'],
                    'Volume': quote['volume'],
                    'Alert': alert_message if alert_triggered else ""
                })
        except Exception as e:
            watchlist_data.append({
                'Symbol': symbol,
                'Price': 0,
                'Change': 0,
                'Change %': 0,
                'Volume': 0,
                'Alert': f"Error: {str(e)}"
            })
    
    if watchlist_data:
        # Display watchlist table
        df = pd.DataFrame(watchlist_data)
        
        # Show alerts if any
        alerts = df[df['Alert'] != '']['Alert'].tolist()
        if alerts:
            st.subheader("🚨 Price Alerts")
            for alert in alerts:
                st.error(alert)
        
        # Format the display
        for index, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 3, 1])
            
            with col1:
                st.metric(
                    label=row['Symbol'],
                    value=f"${row['Price']:.2f}",
                    delta=f"{row['Change %']:.2f}%"
                )
            
            with col2:
                st.write(f"Volume: {row['Volume']:,.0f}")
            
            with col3:
                # Mini chart button
                if st.button(f"📈 Chart", key=f"chart_{row['Symbol']}"):
                    st.session_state.selected_chart_symbol = row['Symbol']
            
            with col4:
                # Set alert button
                if st.button(f"🔔 Alert", key=f"alert_{row['Symbol']}"):
                    st.session_state.selected_alert_symbol = row['Symbol']
            
            with col5:
                # Remove from watchlist
                if st.button(f"❌ Remove", key=f"remove_{row['Symbol']}"):
                    st.session_state.watchlist.remove(row['Symbol'])
                    if row['Symbol'] in st.session_state.price_alerts:
                        del st.session_state.price_alerts[row['Symbol']]
                    # Remove from database if user is logged in
                    if user:
                        data_persistence.remove_watchlist_item(user['id'], row['Symbol'])
                    st.rerun()
            
            with col6:
                pass
        
        # Watchlist performance chart
        st.subheader("Watchlist Performance")
        
        period = st.selectbox(
            "Chart Period",
            ["1d", "5d", "1mo", "3mo"],
            index=2
        )
        
        fig = go.Figure()
        
        for symbol in st.session_state.watchlist[:10]:  # Limit to 10 for readability
            try:
                data = data_fetcher.get_stock_data(symbol, period)
                if not data.empty:
                    # Calculate percentage change from first day
                    first_price = data['Close'].iloc[0]
                    pct_change = ((data['Close'] - first_price) / first_price) * 100
                    
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=pct_change,
                            mode='lines',
                            name=symbol,
                            line=dict(width=2)
                        )
                    )
            except:
                continue
        
        fig.update_layout(
            title=f"Watchlist Performance ({period}) - % Change",
            xaxis_title="Date",
            yaxis_title="Percentage Change (%)",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Individual stock chart
if 'selected_chart_symbol' in st.session_state:
    symbol = st.session_state.selected_chart_symbol
    st.subheader(f"{symbol} - Detailed Chart")
    
    chart_period = st.selectbox(
        "Chart Period",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
        index=2,
        key="chart_period"
    )
    
    try:
        data = data_fetcher.get_stock_data(symbol, chart_period)
        if not data.empty:
            fig = go.Figure(data=go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name=symbol
            ))
            
            fig.update_layout(
                title=f"{symbol} Price Chart ({chart_period})",
                height=500,
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"No data available for {symbol}")
    except Exception as e:
        st.error(f"Error loading chart for {symbol}: {str(e)}")
    
    if st.button("Close Chart"):
        del st.session_state.selected_chart_symbol
        st.rerun()

# Price alerts management
if 'selected_alert_symbol' in st.session_state:
    symbol = st.session_state.selected_alert_symbol
    st.subheader(f"Set Price Alert for {symbol}")
    
    # Get current price
    try:
        quote = data_fetcher.get_real_time_quote(symbol)
        current_price = quote['price'] if quote else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            alert_type = st.selectbox("Alert Type", ["above", "below"])
        
        with col2:
            alert_price = st.number_input(
                f"Alert Price (Current: ${current_price:.2f})",
                min_value=0.01,
                value=current_price,
                step=0.01,
                format="%.2f"
            )
        
        with col3:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("Set Alert"):
                if symbol not in st.session_state.price_alerts:
                    st.session_state.price_alerts[symbol] = []
                
                alert = {
                    'type': alert_type,
                    'price': alert_price,
                    'created_at': datetime.now().isoformat()
                }
                
                st.session_state.price_alerts[symbol].append(alert)
                st.success(f"Alert set: {symbol} {alert_type} ${alert_price:.2f}")
        
        # Show existing alerts
        if symbol in st.session_state.price_alerts and st.session_state.price_alerts[symbol]:
            st.write("**Existing Alerts:**")
            for i, alert in enumerate(st.session_state.price_alerts[symbol]):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{alert['type'].title()} ${alert['price']:.2f}")
                with col2:
                    if st.button("Remove", key=f"remove_alert_{symbol}_{i}"):
                        st.session_state.price_alerts[symbol].pop(i)
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error setting alert: {str(e)}")
    
    if st.button("Close Alert Setup"):
        del st.session_state.selected_alert_symbol
        st.rerun()

# Watchlist statistics
if st.session_state.watchlist:
    st.subheader("Watchlist Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gainers = len([stock for stock in watchlist_data if stock['Change %'] > 0])
        st.metric("Gainers", gainers)
    
    with col2:
        losers = len([stock for stock in watchlist_data if stock['Change %'] < 0])
        st.metric("Losers", losers)
    
    with col3:
        total_alerts = sum(len(alerts) for alerts in st.session_state.price_alerts.values())
        st.metric("Active Alerts", total_alerts)

else:
    st.info("Your watchlist is empty. Add some stocks to get started!")
    
    # Suggest popular stocks
    st.subheader("Popular Stocks to Watch")
    
    popular_stocks = [
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA'
    ]
    
    cols = st.columns(4)
    for i, symbol in enumerate(popular_stocks):
        with cols[i % 4]:
            if st.button(f"Add {symbol}", key=f"add_popular_{symbol}"):
                st.session_state.watchlist.append(symbol)
                st.success(f"Added {symbol} to watchlist!")
                st.rerun()

# Auto-refresh option
with st.sidebar:
    st.subheader("Settings")
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds")
    
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()
    
    if st.button("Refresh Watchlist"):
        st.rerun()
    
    # Export watchlist
    if st.session_state.watchlist:
        st.subheader("Export Watchlist")
        watchlist_text = "\n".join(st.session_state.watchlist)
        st.download_button(
            label="Download Watchlist",
            data=watchlist_text,
            file_name=f"watchlist_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    
    # Clear watchlist
    if st.session_state.watchlist:
        if st.button("Clear Watchlist", type="secondary"):
            st.session_state.watchlist = []
            st.session_state.price_alerts = {}
            st.success("Watchlist cleared!")
            st.rerun()
