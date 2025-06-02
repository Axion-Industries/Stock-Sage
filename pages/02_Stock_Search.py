import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from utils.data_fetcher import DataFetcher
from utils.technical_analysis import TechnicalAnalysis

st.set_page_config(page_title="Stock Search", page_icon="🔍", layout="wide")

# Initialize components
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = DataFetcher()

if 'technical_analysis' not in st.session_state:
    st.session_state.technical_analysis = TechnicalAnalysis()

data_fetcher = st.session_state.data_fetcher
ta = st.session_state.technical_analysis

st.title("🔍 Stock Search & Analysis")

# Search functionality
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    search_query = st.text_input(
        "Search for stocks",
        placeholder="Type stock symbol or company name (e.g., AAPL, Apple, MSFT)",
        help="Enter a stock symbol or start typing a company name"
    )

with col2:
    period = st.selectbox(
        "Time Period",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3  # Default to 3mo
    )

with col3:
    chart_type = st.selectbox(
        "Chart Type",
        ["Candlestick", "Line", "Area"],
        index=0
    )

# Search suggestions
if search_query:
    suggestions = data_fetcher.search_symbols(search_query)
    if suggestions:
        st.write("**Suggestions:**")
        suggestion_cols = st.columns(min(len(suggestions), 4))
        
        for i, (symbol, name) in enumerate(suggestions[:4]):
            with suggestion_cols[i]:
                if st.button(f"{symbol} - {name[:20]}...", key=f"suggest_{i}"):
                    st.session_state.selected_symbol = symbol

# Selected symbol
selected_symbol = None
if 'selected_symbol' in st.session_state:
    selected_symbol = st.session_state.selected_symbol
elif search_query and len(search_query) >= 1:
    # Try to use the search query as symbol
    if data_fetcher.validate_symbol(search_query.upper()):
        selected_symbol = search_query.upper()

# Display stock analysis if symbol is selected
if selected_symbol:
    try:
        # Get stock data
        stock_data = data_fetcher.get_stock_data(selected_symbol, period)
        stock_info = data_fetcher.get_stock_info(selected_symbol)
        
        if stock_data.empty:
            st.error(f"No data found for symbol: {selected_symbol}")
        else:
            # Stock header
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'longName' in stock_info:
                    st.subheader(f"{stock_info['longName']} ({selected_symbol})")
                else:
                    st.subheader(f"{selected_symbol}")
            
            # Current price and metrics
            current_price = stock_data['Close'].iloc[-1]
            prev_close = stock_info.get('previousClose', stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price)
            change = current_price - prev_close
            pct_change = (change / prev_close) * 100
            
            with col2:
                st.metric(
                    "Current Price",
                    f"${current_price:.2f}",
                    f"{change:+.2f} ({pct_change:+.2f}%)"
                )
            
            with col3:
                if 'marketCap' in stock_info and stock_info['marketCap']:
                    market_cap = stock_info['marketCap'] / 1e9
                    st.metric("Market Cap", f"${market_cap:.2f}B")
                else:
                    st.metric("Market Cap", "N/A")
            
            with col4:
                volume = stock_data['Volume'].iloc[-1]
                avg_volume = stock_data['Volume'].rolling(20).mean().iloc[-1]
                st.metric(
                    "Volume",
                    f"{volume:,.0f}",
                    f"{((volume/avg_volume - 1) * 100):+.1f}% vs avg" if not pd.isna(avg_volume) else ""
                )
            
            # Chart options
            st.subheader("Price Chart")
            
            chart_options = st.columns(4)
            with chart_options[0]:
                show_volume = st.checkbox("Show Volume", value=True)
            with chart_options[1]:
                show_ma = st.checkbox("Moving Averages", value=False)
            with chart_options[2]:
                show_bb = st.checkbox("Bollinger Bands", value=False)
            with chart_options[3]:
                show_indicators = st.checkbox("Technical Indicators", value=False)
            
            # Create chart based on type
            if chart_type == "Candlestick":
                # Create candlestick chart with subplots
                rows = 2 if show_volume else 1
                row_heights = [0.7, 0.3] if show_volume else [1.0]
                
                fig = make_subplots(
                    rows=rows, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    subplot_titles=[f'{selected_symbol} Price'] + (['Volume'] if show_volume else []),
                    row_heights=row_heights
                )
                
                # Candlestick
                fig.add_trace(
                    go.Candlestick(
                        x=stock_data.index,
                        open=stock_data['Open'],
                        high=stock_data['High'],
                        low=stock_data['Low'],
                        close=stock_data['Close'],
                        name=selected_symbol
                    ),
                    row=1, col=1
                )
                
                # Moving averages
                if show_ma:
                    sma_20 = ta.calculate_sma(stock_data['Close'], 20)
                    sma_50 = ta.calculate_sma(stock_data['Close'], 50)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=sma_20,
                            mode='lines',
                            name='SMA 20',
                            line=dict(color='orange', width=1)
                        ),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=sma_50,
                            mode='lines',
                            name='SMA 50',
                            line=dict(color='blue', width=1)
                        ),
                        row=1, col=1
                    )
                
                # Bollinger Bands
                if show_bb:
                    bb = ta.calculate_bollinger_bands(stock_data['Close'])
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=bb['upper'],
                            mode='lines',
                            name='BB Upper',
                            line=dict(color='red', dash='dash', width=1)
                        ),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=bb['lower'],
                            mode='lines',
                            name='BB Lower',
                            line=dict(color='red', dash='dash', width=1),
                            fill='tonexty',
                            fillcolor='rgba(255,0,0,0.05)'
                        ),
                        row=1, col=1
                    )
                
                # Volume
                if show_volume:
                    colors = ['red' if close < open else 'green' 
                             for close, open in zip(stock_data['Close'], stock_data['Open'])]
                    
                    fig.add_trace(
                        go.Bar(
                            x=stock_data.index,
                            y=stock_data['Volume'],
                            name='Volume',
                            marker_color=colors,
                            opacity=0.7
                        ),
                        row=2, col=1
                    )
                
                fig.update_layout(
                    height=600,
                    xaxis_rangeslider_visible=False,
                    showlegend=True
                )
                
            elif chart_type == "Line":
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=stock_data['Close'],
                        mode='lines',
                        name=f'{selected_symbol} Close',
                        line=dict(width=2)
                    )
                )
                
                if show_ma:
                    sma_20 = ta.calculate_sma(stock_data['Close'], 20)
                    sma_50 = ta.calculate_sma(stock_data['Close'], 50)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=sma_20,
                            mode='lines',
                            name='SMA 20',
                            line=dict(color='orange')
                        )
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=sma_50,
                            mode='lines',
                            name='SMA 50',
                            line=dict(color='blue')
                        )
                    )
                
                fig.update_layout(
                    title=f'{selected_symbol} Price Chart',
                    height=500
                )
            
            else:  # Area chart
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=stock_data['Close'],
                        mode='lines',
                        name=f'{selected_symbol} Close',
                        fill='tonexty',
                        line=dict(width=2)
                    )
                )
                
                fig.update_layout(
                    title=f'{selected_symbol} Price Chart',
                    height=500
                )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Technical indicators section
            if show_indicators:
                st.subheader("Technical Indicators")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # RSI
                    rsi = ta.calculate_rsi(stock_data['Close'])
                    current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 0
                    
                    rsi_status = "Neutral"
                    if current_rsi > 70:
                        rsi_status = "Overbought"
                    elif current_rsi < 30:
                        rsi_status = "Oversold"
                    
                    st.metric("RSI (14)", f"{current_rsi:.2f}", rsi_status)
                    
                    # MACD
                    macd_data = ta.calculate_macd(stock_data['Close'])
                    macd_current = macd_data['macd'].iloc[-1]
                    signal_current = macd_data['signal'].iloc[-1]
                    
                    macd_signal = "Bullish" if macd_current > signal_current else "Bearish"
                    st.metric("MACD Signal", macd_signal)
                
                with col2:
                    # Support and Resistance
                    levels = ta.get_support_resistance_levels(stock_data)
                    if levels['resistance']:
                        st.metric("Resistance", f"${levels['resistance'][0]:.2f}")
                    if levels['support']:
                        st.metric("Support", f"${levels['support'][0]:.2f}")
                    
                    # Pivot Points
                    pivot_data = ta.calculate_pivot_points(stock_data)
                    if pivot_data:
                        st.metric("Pivot Point", f"${pivot_data['pivot']:.2f}")
            
            # Company information
            if stock_info:
                st.subheader("Company Information")
                
                info_cols = st.columns(3)
                
                with info_cols[0]:
                    if 'sector' in stock_info:
                        st.write(f"**Sector:** {stock_info['sector']}")
                    if 'industry' in stock_info:
                        st.write(f"**Industry:** {stock_info['industry']}")
                    if 'country' in stock_info:
                        st.write(f"**Country:** {stock_info['country']}")
                
                with info_cols[1]:
                    if 'marketCap' in stock_info and stock_info['marketCap']:
                        market_cap = stock_info['marketCap'] / 1e9
                        st.write(f"**Market Cap:** ${market_cap:.2f}B")
                    if 'trailingPE' in stock_info and stock_info['trailingPE']:
                        st.write(f"**P/E Ratio:** {stock_info['trailingPE']:.2f}")
                    if 'dividendYield' in stock_info and stock_info['dividendYield']:
                        div_yield = stock_info['dividendYield'] * 100
                        st.write(f"**Dividend Yield:** {div_yield:.2f}%")
                
                with info_cols[2]:
                    if 'fiftyTwoWeekHigh' in stock_info:
                        st.write(f"**52W High:** ${stock_info['fiftyTwoWeekHigh']:.2f}")
                    if 'fiftyTwoWeekLow' in stock_info:
                        st.write(f"**52W Low:** ${stock_info['fiftyTwoWeekLow']:.2f}")
                    if 'beta' in stock_info and stock_info['beta']:
                        st.write(f"**Beta:** {stock_info['beta']:.2f}")
                
                # Company description
                if 'longBusinessSummary' in stock_info:
                    st.subheader("Business Summary")
                    st.write(stock_info['longBusinessSummary'])
            
            # Add to watchlist button
            if st.button("Add to Watchlist", type="primary"):
                if 'watchlist' not in st.session_state:
                    st.session_state.watchlist = []
                
                if selected_symbol not in st.session_state.watchlist:
                    st.session_state.watchlist.append(selected_symbol)
                    st.success(f"Added {selected_symbol} to watchlist!")
                else:
                    st.warning(f"{selected_symbol} is already in your watchlist.")
    
    except Exception as e:
        st.error(f"Error loading data for {selected_symbol}: {str(e)}")

else:
    st.info("Enter a stock symbol above to search and analyze stocks.")
    
    # Show popular stocks as examples
    st.subheader("Popular Stocks")
    
    popular_stocks = [
        ('AAPL', 'Apple Inc.'),
        ('GOOGL', 'Alphabet Inc.'),
        ('MSFT', 'Microsoft Corporation'),
        ('AMZN', 'Amazon.com Inc.'),
        ('TSLA', 'Tesla Inc.'),
        ('META', 'Meta Platforms Inc.'),
        ('NFLX', 'Netflix Inc.'),
        ('NVDA', 'NVIDIA Corporation')
    ]
    
    cols = st.columns(4)
    for i, (symbol, name) in enumerate(popular_stocks):
        with cols[i % 4]:
            if st.button(f"{symbol}\n{name}", key=f"popular_{i}"):
                st.session_state.selected_symbol = symbol
                st.rerun()
