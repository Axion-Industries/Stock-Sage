import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

class TechnicalAnalysis:
    def __init__(self):
        pass
    
    def calculate_sma(self, data, window):
        """Calculate Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    def calculate_ema(self, data, window):
        """Calculate Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    def calculate_rsi(self, data, window=14):
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        macd = ema_fast - ema_slow
        macd_signal = self.calculate_ema(macd, signal)
        macd_histogram = macd - macd_signal
        
        return {
            'macd': macd,
            'signal': macd_signal,
            'histogram': macd_histogram
        }
    
    def calculate_bollinger_bands(self, data, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(data, window)
        std = data.rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    def calculate_stochastic(self, high, low, close, k_window=14, d_window=3):
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    def calculate_williams_r(self, high, low, close, window=14):
        """Calculate Williams %R"""
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return williams_r
    
    def calculate_atr(self, high, low, close, window=14):
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = true_range.rolling(window=window).mean()
        
        return atr
    
    def calculate_volume_indicators(self, data, volume):
        """Calculate volume-based indicators"""
        # On-Balance Volume (OBV)
        obv = []
        obv_value = 0
        
        for i in range(len(data)):
            if i == 0:
                obv.append(volume.iloc[i])
                obv_value = volume.iloc[i]
            else:
                if data.iloc[i] > data.iloc[i-1]:
                    obv_value += volume.iloc[i]
                elif data.iloc[i] < data.iloc[i-1]:
                    obv_value -= volume.iloc[i]
                obv.append(obv_value)
        
        obv_series = pd.Series(obv, index=data.index)
        
        # Volume SMA
        volume_sma = volume.rolling(window=20).mean()
        
        return {
            'obv': obv_series,
            'volume_sma': volume_sma
        }
    
    def create_candlestick_chart(self, data, symbol, indicators=None):
        """Create interactive candlestick chart with indicators"""
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=[f'{symbol} Price', 'Volume', 'Technical Indicators'],
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name=symbol
            ),
            row=1, col=1
        )
        
        # Add moving averages if requested
        if indicators and 'sma_20' in indicators:
            sma_20 = self.calculate_sma(data['Close'], 20)
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=sma_20,
                    mode='lines',
                    name='SMA 20',
                    line=dict(color='orange')
                ),
                row=1, col=1
            )
        
        if indicators and 'sma_50' in indicators:
            sma_50 = self.calculate_sma(data['Close'], 50)
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=sma_50,
                    mode='lines',
                    name='SMA 50',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
        
        if indicators and 'ema_12' in indicators:
            ema_12 = self.calculate_ema(data['Close'], 12)
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=ema_12,
                    mode='lines',
                    name='EMA 12',
                    line=dict(color='green')
                ),
                row=1, col=1
            )
        
        # Bollinger Bands
        if indicators and 'bollinger' in indicators:
            bb = self.calculate_bollinger_bands(data['Close'])
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb['upper'],
                    mode='lines',
                    name='BB Upper',
                    line=dict(color='red', dash='dash')
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb['lower'],
                    mode='lines',
                    name='BB Lower',
                    line=dict(color='red', dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(255,0,0,0.1)'
                ),
                row=1, col=1
            )
        
        # Volume chart
        colors = ['red' if close < open else 'green' 
                 for close, open in zip(data['Close'], data['Open'])]
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        # RSI
        if indicators and 'rsi' in indicators:
            rsi = self.calculate_rsi(data['Close'])
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=rsi,
                    mode='lines',
                    name='RSI',
                    line=dict(color='purple')
                ),
                row=3, col=1
            )
            
            # Add RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        # MACD
        if indicators and 'macd' in indicators:
            macd_data = self.calculate_macd(data['Close'])
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=macd_data['macd'],
                    mode='lines',
                    name='MACD',
                    line=dict(color='blue')
                ),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=macd_data['signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color='red')
                ),
                row=3, col=1
            )
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Technical Analysis',
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="Indicator", row=3, col=1)
        
        return fig
    
    def create_rsi_chart(self, data, symbol):
        """Create RSI chart"""
        rsi = self.calculate_rsi(data['Close'])
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=rsi,
                mode='lines',
                name='RSI',
                line=dict(color='purple')
            )
        )
        
        # Add overbought and oversold levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
        fig.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="Midline (50)")
        
        fig.update_layout(
            title=f'{symbol} RSI (14-period)',
            xaxis_title='Date',
            yaxis_title='RSI',
            height=400,
            yaxis=dict(range=[0, 100])
        )
        
        return fig
    
    def create_macd_chart(self, data, symbol):
        """Create MACD chart"""
        macd_data = self.calculate_macd(data['Close'])
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=['MACD Line & Signal', 'MACD Histogram'],
            row_heights=[0.7, 0.3]
        )
        
        # MACD line and signal
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=macd_data['macd'],
                mode='lines',
                name='MACD',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=macd_data['signal'],
                mode='lines',
                name='Signal',
                line=dict(color='red')
            ),
            row=1, col=1
        )
        
        # MACD histogram
        colors = ['green' if val >= 0 else 'red' for val in macd_data['histogram']]
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=macd_data['histogram'],
                name='Histogram',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title=f'{symbol} MACD (12, 26, 9)',
            height=600,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="MACD", row=1, col=1)
        fig.update_yaxes(title_text="Histogram", row=2, col=1)
        
        return fig
    
    def get_support_resistance_levels(self, data, window=20):
        """Calculate support and resistance levels"""
        highs = data['High'].rolling(window=window).max()
        lows = data['Low'].rolling(window=window).min()
        
        # Find local maxima and minima
        resistance_levels = []
        support_levels = []
        
        for i in range(window, len(data) - window):
            # Check for resistance (local high)
            if data['High'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(data['High'].iloc[i])
            
            # Check for support (local low)
            if data['Low'].iloc[i] == lows.iloc[i]:
                support_levels.append(data['Low'].iloc[i])
        
        # Get unique levels
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:5]
        support_levels = sorted(list(set(support_levels)))[:5]
        
        return {
            'resistance': resistance_levels,
            'support': support_levels
        }
    
    def calculate_pivot_points(self, data):
        """Calculate pivot points for the latest trading day"""
        if len(data) == 0:
            return None
        
        latest = data.iloc[-1]
        high = latest['High']
        low = latest['Low']
        close = latest['Close']
        
        # Classic pivot points
        pivot = (high + low + close) / 3
        
        # Resistance levels
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        # Support levels
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
