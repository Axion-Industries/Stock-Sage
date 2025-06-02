import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class DataFetcher:
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
        
    @st.cache_data(ttl=300)
    def get_stock_data(_self, symbol, period="1y"):
        """
        Fetch stock data for a given symbol and period
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            period (str): Period for data ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        
        Returns:
            pandas.DataFrame: Stock data with OHLCV
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_stock_info(_self, symbol):
        """
        Get detailed stock information
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info
        except Exception as e:
            st.error(f"Error fetching info for {symbol}: {str(e)}")
            return {}
    
    @st.cache_data(ttl=300)
    def get_multiple_stocks(_self, symbols, period="1d"):
        """
        Fetch data for multiple stocks
        
        Args:
            symbols (list): List of stock symbols
            period (str): Period for data
            
        Returns:
            dict: Dictionary with symbol as key and data as value
        """
        stock_data = {}
        for symbol in symbols:
            try:
                data = _self.get_stock_data(symbol, period)
                if not data.empty:
                    stock_data[symbol] = data
            except Exception as e:
                continue
        return stock_data
    
    def get_real_time_quote(self, symbol):
        """
        Get real-time quote for a symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Real-time quote data
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if data.empty:
                return None
                
            latest = data.iloc[-1]
            previous_close = ticker.info.get('previousClose', latest['Open'])
            
            return {
                'symbol': symbol.upper(),
                'price': latest['Close'],
                'change': latest['Close'] - previous_close,
                'percent_change': ((latest['Close'] - previous_close) / previous_close) * 100,
                'volume': latest['Volume'],
                'timestamp': data.index[-1]
            }
        except Exception as e:
            st.error(f"Error fetching real-time data for {symbol}: {str(e)}")
            return None
    
    @st.cache_data(ttl=300)
    def search_symbols(_self, query):
        """
        Search for stock symbols based on query
        
        Args:
            query (str): Search query
            
        Returns:
            list: List of matching symbols and names
        """
        # Common stock symbols for autocomplete
        common_stocks = [
            ('AAPL', 'Apple Inc.'),
            ('GOOGL', 'Alphabet Inc.'),
            ('MSFT', 'Microsoft Corporation'),
            ('AMZN', 'Amazon.com Inc.'),
            ('TSLA', 'Tesla Inc.'),
            ('META', 'Meta Platforms Inc.'),
            ('NFLX', 'Netflix Inc.'),
            ('NVDA', 'NVIDIA Corporation'),
            ('AMD', 'Advanced Micro Devices'),
            ('INTC', 'Intel Corporation'),
            ('CRM', 'Salesforce Inc.'),
            ('ORCL', 'Oracle Corporation'),
            ('IBM', 'International Business Machines'),
            ('CSCO', 'Cisco Systems Inc.'),
            ('ADBE', 'Adobe Inc.'),
            ('PYPL', 'PayPal Holdings Inc.'),
            ('SHOP', 'Shopify Inc.'),
            ('SQ', 'Block Inc.'),
            ('UBER', 'Uber Technologies Inc.'),
            ('LYFT', 'Lyft Inc.'),
            ('SNAP', 'Snap Inc.'),
            ('TWTR', 'Twitter Inc.'),
            ('ZOOM', 'Zoom Video Communications'),
            ('DOCU', 'DocuSign Inc.'),
            ('CRWD', 'CrowdStrike Holdings Inc.'),
            ('OKTA', 'Okta Inc.'),
            ('SNOW', 'Snowflake Inc.'),
            ('PLTR', 'Palantir Technologies Inc.'),
            ('COIN', 'Coinbase Global Inc.'),
            ('RBLX', 'Roblox Corporation'),
            ('RIVN', 'Rivian Automotive Inc.'),
            ('LCID', 'Lucid Group Inc.'),
            ('SOFI', 'SoFi Technologies Inc.'),
            ('HOOD', 'Robinhood Markets Inc.'),
            ('GME', 'GameStop Corp.'),
            ('AMC', 'AMC Entertainment Holdings'),
            ('BB', 'BlackBerry Limited'),
            ('NOK', 'Nokia Corporation'),
            ('SNDL', 'Sundial Growers Inc.'),
            ('F', 'Ford Motor Company'),
            ('GM', 'General Motors Company'),
            ('BAC', 'Bank of America Corporation'),
            ('JPM', 'JPMorgan Chase & Co.'),
            ('WFC', 'Wells Fargo & Company'),
            ('GS', 'The Goldman Sachs Group'),
            ('MS', 'Morgan Stanley'),
            ('V', 'Visa Inc.'),
            ('MA', 'Mastercard Incorporated'),
            ('JNJ', 'Johnson & Johnson'),
            ('PFE', 'Pfizer Inc.'),
            ('MRNA', 'Moderna Inc.'),
            ('BNTX', 'BioNTech SE'),
            ('KO', 'The Coca-Cola Company'),
            ('PEP', 'PepsiCo Inc.'),
            ('MCD', 'McDonald\'s Corporation'),
            ('SBUX', 'Starbucks Corporation'),
            ('WMT', 'Walmart Inc.'),
            ('TGT', 'Target Corporation'),
            ('HD', 'The Home Depot Inc.'),
            ('LOW', 'Lowe\'s Companies Inc.'),
            ('DIS', 'The Walt Disney Company'),
            ('NFLX', 'Netflix Inc.'),
            ('T', 'AT&T Inc.'),
            ('VZ', 'Verizon Communications Inc.'),
            ('XOM', 'Exxon Mobil Corporation'),
            ('CVX', 'Chevron Corporation'),
            ('GLD', 'SPDR Gold Shares'),
            ('SLV', 'iShares Silver Trust'),
            ('SPY', 'SPDR S&P 500 ETF Trust'),
            ('QQQ', 'Invesco QQQ Trust'),
            ('IWM', 'iShares Russell 2000 ETF'),
            ('VTI', 'Vanguard Total Stock Market ETF'),
            ('VOO', 'Vanguard S&P 500 ETF'),
        ]
        
        if not query:
            return []
        
        query = query.upper()
        matches = []
        
        for symbol, name in common_stocks:
            if query in symbol or query in name.upper():
                matches.append((symbol, name))
        
        return matches[:20]  # Return top 20 matches
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_market_indices(_self):
        """
        Get major market indices data
        
        Returns:
            dict: Market indices data
        """
        indices = {
            'S&P 500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DOW': '^DJI',
            'Russell 2000': '^RUT',
            'VIX': '^VIX'
        }
        
        indices_data = {}
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                # Get 1 day data with 5-minute intervals for intraday chart
                data = ticker.history(period="1d", interval="5m")
                
                # Also get basic info
                info = ticker.info
                current_price = info.get('regularMarketPrice', 0)
                previous_close = info.get('previousClose', 0)
                
                if current_price == 0 and not data.empty:
                    current_price = data['Close'].iloc[-1]
                
                if previous_close == 0 and not data.empty and len(data) > 1:
                    previous_close = data['Close'].iloc[0]
                
                if current_price > 0 and previous_close > 0:
                    change = current_price - previous_close
                    pct_change = (change / previous_close) * 100
                    
                    indices_data[name] = {
                        'symbol': symbol,
                        'price': current_price,
                        'change': change,
                        'percent_change': pct_change,
                        'data': data
                    }
            except Exception as e:
                # Fallback to simple daily data
                try:
                    ticker = yf.Ticker(symbol)
                    simple_data = ticker.history(period="2d")
                    if len(simple_data) >= 2:
                        current_price = simple_data['Close'].iloc[-1]
                        previous_close = simple_data['Close'].iloc[-2]
                        change = current_price - previous_close
                        pct_change = (change / previous_close) * 100
                        
                        indices_data[name] = {
                            'symbol': symbol,
                            'price': current_price,
                            'change': change,
                            'percent_change': pct_change,
                            'data': simple_data
                        }
                except:
                    continue
        
        return indices_data
    
    def validate_symbol(self, symbol):
        """
        Validate if a stock symbol exists
        
        Args:
            symbol (str): Stock symbol to validate
            
        Returns:
            bool: True if symbol exists, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            return not data.empty
        except:
            return False
