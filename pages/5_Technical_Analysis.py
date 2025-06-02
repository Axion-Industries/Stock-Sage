import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from utils.data_fetcher import DataFetcher
from utils.technical_analysis import TechnicalAnalysis

st.set_page_config(page_title="Technical Analysis", page_icon="📊", layout="wide")

# Initialize components
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = DataFetcher()

if 'technical_analysis' not in st.session_state:
    st.session_state.technical_analysis = TechnicalAnalysis()

data_fetcher = st.session_state.data_fetcher
ta = st.session_state.technical_analysis

st.title("📊 Technical Analysis")

# Stock selection
col1, col2, col3 = st.columns(3)

with col1:
    symbol = st.text_input("Stock Symbol", value="AAPL", placeholder="Enter symbol").upper()

with col2:
    period = st.selectbox(
        "Time Period",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=2
    )

with col3:
    st.write("")  # Spacer
    st.write("")  # Spacer
    analyze_button = st.button("Analyze", type="primary")

if symbol and (analyze_button or 'current_analysis_symbol' in st.session_state):
    # Store current symbol for persistence
    st.session_state.current_analysis_symbol = symbol
    
    try:
        # Validate symbol and get data
        if not data_fetcher.validate_symbol(symbol):
            st.error(f"Invalid stock symbol: {symbol}")
        else:
            stock_data = data_fetcher.get_stock_data(symbol, period)
            stock_info = data_fetcher.get_stock_info(symbol)
            
            if stock_data.empty:
                st.error(f"No data available for {symbol}")
            else:
                # Display basic info
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    current_price = stock_data['Close'].iloc[-1]
                    prev_close = stock_info.get('previousClose', stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price)
                    change = current_price - prev_close
                    pct_change = (change / prev_close) * 100
                    
                    st.metric(
                        f"{symbol} Price",
                        f"${current_price:.2f}",
                        f"{pct_change:+.2f}%"
                    )
                
                with col2:
                    volume = stock_data['Volume'].iloc[-1]
                    avg_volume = stock_data['Volume'].rolling(20).mean().iloc[-1]
                    vol_ratio = volume / avg_volume if not pd.isna(avg_volume) else 1
                    
                    st.metric(
                        "Volume",
                        f"{volume:,.0f}",
                        f"{((vol_ratio - 1) * 100):+.1f}% vs avg"
                    )
                
                with col3:
                    high_52w = stock_data['High'].rolling(252).max().iloc[-1]
                    low_52w = stock_data['Low'].rolling(252).min().iloc[-1]
                    st.metric("52W High", f"${high_52w:.2f}")
                    st.metric("52W Low", f"${low_52w:.2f}")
                
                with col4:
                    # Market cap from info
                    if 'marketCap' in stock_info and stock_info['marketCap']:
                        market_cap = stock_info['marketCap'] / 1e9
                        st.metric("Market Cap", f"${market_cap:.2f}B")
                
                # Technical indicators selection
                st.subheader("Technical Indicators")
                
                indicator_cols = st.columns(4)
                
                with indicator_cols[0]:
                    show_ma = st.checkbox("Moving Averages", value=True)
                    show_bb = st.checkbox("Bollinger Bands", value=False)
                
                with indicator_cols[1]:
                    show_rsi = st.checkbox("RSI", value=True)
                    show_macd = st.checkbox("MACD", value=True)
                
                with indicator_cols[2]:
                    show_stoch = st.checkbox("Stochastic", value=False)
                    show_volume = st.checkbox("Volume Analysis", value=True)
                
                with indicator_cols[3]:
                    show_support_resistance = st.checkbox("Support/Resistance", value=True)
                    show_pivot = st.checkbox("Pivot Points", value=False)
                
                # Main chart with candlesticks
                st.subheader("Price Chart with Technical Indicators")
                
                # Determine number of subplots
                subplot_count = 1  # Main price chart
                if show_volume:
                    subplot_count += 1
                if show_rsi:
                    subplot_count += 1
                if show_macd:
                    subplot_count += 1
                if show_stoch:
                    subplot_count += 1
                
                # Create subplot heights
                heights = [0.5]  # Main chart gets 50%
                remaining = 0.5
                if subplot_count > 1:
                    subplot_height = remaining / (subplot_count - 1)
                    heights.extend([subplot_height] * (subplot_count - 1))
                
                # Create subplots
                subplot_titles = [f'{symbol} Price Chart']
                if show_volume:
                    subplot_titles.append('Volume')
                if show_rsi:
                    subplot_titles.append('RSI')
                if show_macd:
                    subplot_titles.append('MACD')
                if show_stoch:
                    subplot_titles.append('Stochastic')
                
                fig = make_subplots(
                    rows=subplot_count,
                    cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.02,
                    subplot_titles=subplot_titles,
                    row_heights=heights
                )
                
                # Main candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=stock_data.index,
                        open=stock_data['Open'],
                        high=stock_data['High'],
                        low=stock_data['Low'],
                        close=stock_data['Close'],
                        name=symbol,
                        showlegend=False
                    ),
                    row=1, col=1
                )
                
                # Moving Averages
                if show_ma:
                    sma_20 = ta.calculate_sma(stock_data['Close'], 20)
                    sma_50 = ta.calculate_sma(stock_data['Close'], 50)
                    ema_12 = ta.calculate_ema(stock_data['Close'], 12)
                    
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
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=ema_12,
                            mode='lines',
                            name='EMA 12',
                            line=dict(color='green', width=1)
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
                            line=dict(color='red', dash='dash', width=1),
                            showlegend=False
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
                            fillcolor='rgba(255,0,0,0.1)',
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                
                # Support and Resistance
                if show_support_resistance:
                    levels = ta.get_support_resistance_levels(stock_data)
                    for level in levels['resistance'][:3]:  # Top 3 resistance levels
                        fig.add_hline(
                            y=level,
                            line_dash="dash",
                            line_color="red",
                            opacity=0.5,
                            row=1, col=1
                        )
                    for level in levels['support'][:3]:  # Top 3 support levels
                        fig.add_hline(
                            y=level,
                            line_dash="dash",
                            line_color="green",
                            opacity=0.5,
                            row=1, col=1
                        )
                
                # Pivot Points
                if show_pivot:
                    pivot_data = ta.calculate_pivot_points(stock_data)
                    if pivot_data:
                        colors = ['purple', 'red', 'red', 'red', 'green', 'green', 'green']
                        levels = [pivot_data['pivot'], pivot_data['r1'], pivot_data['r2'], pivot_data['r3'],
                                 pivot_data['s1'], pivot_data['s2'], pivot_data['s3']]
                        names = ['Pivot', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']
                        
                        for level, color, name in zip(levels, colors, names):
                            fig.add_hline(
                                y=level,
                                line_dash="dot",
                                line_color=color,
                                opacity=0.6,
                                annotation_text=name,
                                row=1, col=1
                            )
                
                current_row = 2
                
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
                            opacity=0.7,
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    
                    # Volume SMA
                    volume_sma = stock_data['Volume'].rolling(20).mean()
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=volume_sma,
                            mode='lines',
                            name='Volume SMA',
                            line=dict(color='blue', width=1),
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    current_row += 1
                
                # RSI
                if show_rsi:
                    rsi = ta.calculate_rsi(stock_data['Close'])
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=rsi,
                            mode='lines',
                            name='RSI',
                            line=dict(color='purple', width=2),
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    
                    # RSI levels
                    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
                    fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=current_row, col=1)
                    current_row += 1
                
                # MACD
                if show_macd:
                    macd_data = ta.calculate_macd(stock_data['Close'])
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=macd_data['macd'],
                            mode='lines',
                            name='MACD',
                            line=dict(color='blue', width=2),
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=macd_data['signal'],
                            mode='lines',
                            name='Signal',
                            line=dict(color='red', width=2),
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    
                    # MACD histogram
                    colors = ['green' if val >= 0 else 'red' for val in macd_data['histogram']]
                    fig.add_trace(
                        go.Bar(
                            x=stock_data.index,
                            y=macd_data['histogram'],
                            name='MACD Histogram',
                            marker_color=colors,
                            opacity=0.6,
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    current_row += 1
                
                # Stochastic
                if show_stoch:
                    stoch_data = ta.calculate_stochastic(
                        stock_data['High'], stock_data['Low'], stock_data['Close']
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=stoch_data['k'],
                            mode='lines',
                            name='%K',
                            line=dict(color='blue', width=2),
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data.index,
                            y=stoch_data['d'],
                            mode='lines',
                            name='%D',
                            line=dict(color='red', width=2),
                            showlegend=False
                        ),
                        row=current_row, col=1
                    )
                    
                    # Stochastic levels
                    fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
                    fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
                
                # Update layout
                fig.update_layout(
                    height=150 * subplot_count + 200,
                    xaxis_rangeslider_visible=False,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Technical Analysis Summary
                st.subheader("Technical Analysis Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Trend Analysis**")
                    
                    # Moving average trend
                    sma_20 = ta.calculate_sma(stock_data['Close'], 20)
                    sma_50 = ta.calculate_sma(stock_data['Close'], 50)
                    
                    current_price = stock_data['Close'].iloc[-1]
                    sma_20_current = sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else 0
                    sma_50_current = sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else 0
                    
                    if current_price > sma_20_current > sma_50_current:
                        trend = "🟢 Bullish"
                    elif current_price < sma_20_current < sma_50_current:
                        trend = "🔴 Bearish"
                    else:
                        trend = "🟡 Neutral"
                    
                    st.write(f"**Trend:** {trend}")
                    st.write(f"Price vs SMA20: {((current_price/sma_20_current - 1) * 100):+.1f}%")
                    st.write(f"Price vs SMA50: {((current_price/sma_50_current - 1) * 100):+.1f}%")
                
                with col2:
                    st.write("**Momentum Indicators**")
                    
                    # RSI analysis
                    rsi = ta.calculate_rsi(stock_data['Close'])
                    current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
                    
                    if current_rsi > 70:
                        rsi_signal = "🔴 Overbought"
                    elif current_rsi < 30:
                        rsi_signal = "🟢 Oversold"
                    else:
                        rsi_signal = "🟡 Neutral"
                    
                    st.write(f"**RSI (14):** {current_rsi:.1f} - {rsi_signal}")
                    
                    # MACD analysis
                    macd_data = ta.calculate_macd(stock_data['Close'])
                    macd_current = macd_data['macd'].iloc[-1]
                    signal_current = macd_data['signal'].iloc[-1]
                    
                    if macd_current > signal_current:
                        macd_signal = "🟢 Bullish"
                    else:
                        macd_signal = "🔴 Bearish"
                    
                    st.write(f"**MACD:** {macd_signal}")
                
                with col3:
                    st.write("**Key Levels**")
                    
                    # Support and resistance
                    levels = ta.get_support_resistance_levels(stock_data)
                    
                    if levels['resistance']:
                        st.write(f"**Resistance:** ${levels['resistance'][0]:.2f}")
                    
                    if levels['support']:
                        st.write(f"**Support:** ${levels['support'][0]:.2f}")
                    
                    # Volatility (ATR)
                    atr = ta.calculate_atr(stock_data['High'], stock_data['Low'], stock_data['Close'])
                    current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
                    atr_pct = (current_atr / current_price) * 100
                    
                    st.write(f"**ATR:** ${current_atr:.2f} ({atr_pct:.1f}%)")
                
                # Pattern Recognition (Basic)
                st.subheader("Pattern Analysis")
                
                patterns = []
                
                # Simple pattern detection
                recent_data = stock_data.tail(20)
                
                # Doji pattern (open ≈ close)
                latest = recent_data.iloc[-1]
                body_size = abs(latest['Close'] - latest['Open'])
                range_size = latest['High'] - latest['Low']
                
                if body_size < (range_size * 0.1):
                    patterns.append("🟡 Doji - Indecision")
                
                # Hammer pattern
                if (latest['Close'] > latest['Open'] and 
                    (latest['Close'] - latest['Open']) < (latest['High'] - latest['Low']) * 0.3 and
                    (latest['Open'] - latest['Low']) > (latest['High'] - latest['Low']) * 0.6):
                    patterns.append("🟢 Hammer - Bullish Reversal")
                
                # Shooting star pattern  
                if (latest['Open'] > latest['Close'] and 
                    (latest['Open'] - latest['Close']) < (latest['High'] - latest['Low']) * 0.3 and
                    (latest['High'] - latest['Open']) > (latest['High'] - latest['Low']) * 0.6):
                    patterns.append("🔴 Shooting Star - Bearish Reversal")
                
                if patterns:
                    for pattern in patterns:
                        st.write(pattern)
                else:
                    st.write("No significant patterns detected")
                
                # Trading signals summary
                st.subheader("Trading Signals Summary")
                
                signals = []
                
                # Trend signals
                if current_price > sma_20_current > sma_50_current:
                    signals.append("🟢 BUY - Strong uptrend")
                elif current_price < sma_20_current < sma_50_current:
                    signals.append("🔴 SELL - Strong downtrend")
                
                # RSI signals
                if current_rsi < 30:
                    signals.append("🟢 BUY - RSI oversold")
                elif current_rsi > 70:
                    signals.append("🔴 SELL - RSI overbought")
                
                # MACD signals
                if macd_current > signal_current and macd_data['macd'].iloc[-2] <= macd_data['signal'].iloc[-2]:
                    signals.append("🟢 BUY - MACD bullish crossover")
                elif macd_current < signal_current and macd_data['macd'].iloc[-2] >= macd_data['signal'].iloc[-2]:
                    signals.append("🔴 SELL - MACD bearish crossover")
                
                if signals:
                    for signal in signals:
                        if "BUY" in signal:
                            st.success(signal)
                        elif "SELL" in signal:
                            st.error(signal)
                        else:
                            st.info(signal)
                else:
                    st.info("🟡 HOLD - No clear trading signals")
                
                # Risk disclaimer
                st.warning("⚠️ **Disclaimer:** This analysis is for educational purposes only and should not be considered as financial advice. Always do your own research and consider consulting with a financial advisor before making investment decisions.")
    
    except Exception as e:
        st.error(f"Error performing technical analysis: {str(e)}")

else:
    st.info("Enter a stock symbol above to begin technical analysis.")
    
    # Show example analysis
    st.subheader("Available Technical Indicators")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Price Indicators:**")
        st.write("• Simple Moving Average (SMA)")
        st.write("• Exponential Moving Average (EMA)")
        st.write("• Bollinger Bands")
        st.write("• Support & Resistance Levels")
        st.write("• Pivot Points")
    
    with col2:
        st.write("**Momentum Indicators:**")
        st.write("• Relative Strength Index (RSI)")
        st.write("• MACD (Moving Average Convergence Divergence)")
        st.write("• Stochastic Oscillator")
        st.write("• Average True Range (ATR)")
        st.write("• Volume Analysis")
    
    st.subheader("Pattern Recognition")
    st.write("Basic candlestick pattern detection including:")
    st.write("• Doji patterns")
    st.write("• Hammer patterns")
    st.write("• Shooting star patterns")
    st.write("• And more...")

# Sidebar tools
with st.sidebar:
    st.subheader("Analysis Tools")
    
    if st.button("Clear Analysis"):
        if 'current_analysis_symbol' in st.session_state:
            del st.session_state.current_analysis_symbol
        st.rerun()
    
    st.subheader("Quick Analysis")
    
    # Popular stocks for quick analysis
    popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META']
    
    for stock in popular_stocks:
        if st.button(f"Analyze {stock}", key=f"quick_{stock}"):
            st.session_state.current_analysis_symbol = stock
            st.rerun()
    
    st.subheader("Market Indices")
    
    indices = ['^GSPC', '^IXIC', '^DJI', '^RUT']
    index_names = ['S&P 500', 'NASDAQ', 'DOW', 'Russell 2000']
    
    for idx, name in zip(indices, index_names):
        if st.button(f"Analyze {name}", key=f"index_{idx}"):
            st.session_state.current_analysis_symbol = idx
            st.rerun()
