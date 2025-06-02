import requests
import pandas as pd
import streamlit as st
from typing import List, Dict, Optional
import json

class StockSymbolFetcher:
    def __init__(self):
        self.symbols_cache = None
        self.cache_file = "stock_symbols_cache.json"
        
    def fetch_nasdaq_symbols(self) -> List[Dict]:
        """Fetch NASDAQ listed symbols"""
        try:
            url = "https://api.nasdaq.com/api/screener/stocks"
            params = {
                'tableonly': 'true',
                'limit': 25000,
                'offset': 0,
                'download': 'true'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'rows' in data['data']:
                    symbols = []
                    for row in data['data']['rows']:
                        symbols.append({
                            'symbol': row.get('symbol', ''),
                            'name': row.get('name', ''),
                            'market': 'NASDAQ',
                            'sector': row.get('sector', ''),
                            'industry': row.get('industry', '')
                        })
                    return symbols
        except Exception as e:
            st.warning(f"Could not fetch NASDAQ symbols: {str(e)}")
        return []
    
    def fetch_nyse_symbols(self) -> List[Dict]:
        """Fetch NYSE listed symbols"""
        try:
            # Alternative approach using FMP API (requires API key)
            # You can request the user to provide an API key for more comprehensive data
            symbols = []
            
            # For now, return a comprehensive list of major NYSE stocks
            major_nyse_stocks = [
                {'symbol': 'AAPL', 'name': 'Apple Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'NFLX', 'name': 'Netflix Inc.', 'market': 'NYSE', 'sector': 'Communication Services'},
                {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'AMD', 'name': 'Advanced Micro Devices', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'INTC', 'name': 'Intel Corporation', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'CRM', 'name': 'Salesforce Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'ORCL', 'name': 'Oracle Corporation', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'IBM', 'name': 'International Business Machines', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'CSCO', 'name': 'Cisco Systems Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'ADBE', 'name': 'Adobe Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'PYPL', 'name': 'PayPal Holdings Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'SHOP', 'name': 'Shopify Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'SQ', 'name': 'Block Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'UBER', 'name': 'Uber Technologies Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'LYFT', 'name': 'Lyft Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'SNAP', 'name': 'Snap Inc.', 'market': 'NYSE', 'sector': 'Communication Services'},
                {'symbol': 'ZOOM', 'name': 'Zoom Video Communications', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'DOCU', 'name': 'DocuSign Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'CRWD', 'name': 'CrowdStrike Holdings Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'OKTA', 'name': 'Okta Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'SNOW', 'name': 'Snowflake Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'PLTR', 'name': 'Palantir Technologies Inc.', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'COIN', 'name': 'Coinbase Global Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'RBLX', 'name': 'Roblox Corporation', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'RIVN', 'name': 'Rivian Automotive Inc.', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'LCID', 'name': 'Lucid Group Inc.', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'SOFI', 'name': 'SoFi Technologies Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'HOOD', 'name': 'Robinhood Markets Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'GME', 'name': 'GameStop Corp.', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'AMC', 'name': 'AMC Entertainment Holdings', 'market': 'NYSE', 'sector': 'Communication Services'},
                {'symbol': 'BB', 'name': 'BlackBerry Limited', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'NOK', 'name': 'Nokia Corporation', 'market': 'NYSE', 'sector': 'Technology'},
                {'symbol': 'F', 'name': 'Ford Motor Company', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'GM', 'name': 'General Motors Company', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'BAC', 'name': 'Bank of America Corporation', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'WFC', 'name': 'Wells Fargo & Company', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'GS', 'name': 'The Goldman Sachs Group', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'MS', 'name': 'Morgan Stanley', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'V', 'name': 'Visa Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'MA', 'name': 'Mastercard Incorporated', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'JNJ', 'name': 'Johnson & Johnson', 'market': 'NYSE', 'sector': 'Healthcare'},
                {'symbol': 'PFE', 'name': 'Pfizer Inc.', 'market': 'NYSE', 'sector': 'Healthcare'},
                {'symbol': 'MRNA', 'name': 'Moderna Inc.', 'market': 'NYSE', 'sector': 'Healthcare'},
                {'symbol': 'BNTX', 'name': 'BioNTech SE', 'market': 'NYSE', 'sector': 'Healthcare'},
                {'symbol': 'KO', 'name': 'The Coca-Cola Company', 'market': 'NYSE', 'sector': 'Consumer Staples'},
                {'symbol': 'PEP', 'name': 'PepsiCo Inc.', 'market': 'NYSE', 'sector': 'Consumer Staples'},
                {'symbol': 'MCD', 'name': 'McDonald\'s Corporation', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'SBUX', 'name': 'Starbucks Corporation', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'WMT', 'name': 'Walmart Inc.', 'market': 'NYSE', 'sector': 'Consumer Staples'},
                {'symbol': 'TGT', 'name': 'Target Corporation', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'HD', 'name': 'The Home Depot Inc.', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'LOW', 'name': 'Lowe\'s Companies Inc.', 'market': 'NYSE', 'sector': 'Consumer Discretionary'},
                {'symbol': 'DIS', 'name': 'The Walt Disney Company', 'market': 'NYSE', 'sector': 'Communication Services'},
                {'symbol': 'T', 'name': 'AT&T Inc.', 'market': 'NYSE', 'sector': 'Communication Services'},
                {'symbol': 'VZ', 'name': 'Verizon Communications Inc.', 'market': 'NYSE', 'sector': 'Communication Services'},
                {'symbol': 'XOM', 'name': 'Exxon Mobil Corporation', 'market': 'NYSE', 'sector': 'Energy'},
                {'symbol': 'CVX', 'name': 'Chevron Corporation', 'market': 'NYSE', 'sector': 'Energy'},
                {'symbol': 'COP', 'name': 'ConocoPhillips', 'market': 'NYSE', 'sector': 'Energy'},
                {'symbol': 'SLB', 'name': 'Schlumberger Limited', 'market': 'NYSE', 'sector': 'Energy'},
                {'symbol': 'HAL', 'name': 'Halliburton Company', 'market': 'NYSE', 'sector': 'Energy'},
                {'symbol': 'BRK.A', 'name': 'Berkshire Hathaway Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'BRK.B', 'name': 'Berkshire Hathaway Inc.', 'market': 'NYSE', 'sector': 'Financial Services'},
                {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF Trust', 'market': 'NYSE', 'sector': 'ETF'},
                {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust', 'market': 'NYSE', 'sector': 'ETF'},
                {'symbol': 'IWM', 'name': 'iShares Russell 2000 ETF', 'market': 'NYSE', 'sector': 'ETF'},
                {'symbol': 'VTI', 'name': 'Vanguard Total Stock Market ETF', 'market': 'NYSE', 'sector': 'ETF'},
                {'symbol': 'VOO', 'name': 'Vanguard S&P 500 ETF', 'market': 'NYSE', 'sector': 'ETF'},
                {'symbol': 'GLD', 'name': 'SPDR Gold Shares', 'market': 'NYSE', 'sector': 'ETF'},
                {'symbol': 'SLV', 'name': 'iShares Silver Trust', 'market': 'NYSE', 'sector': 'ETF'},
            ]
            
            return major_nyse_stocks
            
        except Exception as e:
            st.warning(f"Could not fetch NYSE symbols: {str(e)}")
        return []
    
    def fetch_international_symbols(self) -> List[Dict]:
        """Fetch international stock symbols"""
        international_stocks = [
            # Major international stocks available on US exchanges
            {'symbol': 'ASML', 'name': 'ASML Holding N.V.', 'market': 'International', 'sector': 'Technology'},
            {'symbol': 'SAP', 'name': 'SAP SE', 'market': 'International', 'sector': 'Technology'},
            {'symbol': 'TSM', 'name': 'Taiwan Semiconductor', 'market': 'International', 'sector': 'Technology'},
            {'symbol': 'TM', 'name': 'Toyota Motor Corporation', 'market': 'International', 'sector': 'Consumer Discretionary'},
            {'symbol': 'SONY', 'name': 'Sony Group Corporation', 'market': 'International', 'sector': 'Technology'},
            {'symbol': 'NVO', 'name': 'Novo Nordisk A/S', 'market': 'International', 'sector': 'Healthcare'},
            {'symbol': 'NESN', 'name': 'Nestlé S.A.', 'market': 'International', 'sector': 'Consumer Staples'},
            {'symbol': 'UL', 'name': 'Unilever PLC', 'market': 'International', 'sector': 'Consumer Staples'},
            {'symbol': 'BABA', 'name': 'Alibaba Group Holding', 'market': 'International', 'sector': 'Technology'},
            {'symbol': 'PDD', 'name': 'PDD Holdings Inc.', 'market': 'International', 'sector': 'Technology'},
            {'symbol': 'JD', 'name': 'JD.com Inc.', 'market': 'International', 'sector': 'Technology'},
            {'symbol': 'NIO', 'name': 'NIO Inc.', 'market': 'International', 'sector': 'Consumer Discretionary'},
            {'symbol': 'LI', 'name': 'Li Auto Inc.', 'market': 'International', 'sector': 'Consumer Discretionary'},
            {'symbol': 'XPEV', 'name': 'XPeng Inc.', 'market': 'International', 'sector': 'Consumer Discretionary'},
            {'symbol': 'SPOT', 'name': 'Spotify Technology S.A.', 'market': 'International', 'sector': 'Communication Services'},
        ]
        return international_stocks
    
    def get_all_symbols(self, force_refresh: bool = False) -> List[Dict]:
        """Get all available stock symbols"""
        if self.symbols_cache is not None and not force_refresh:
            return self.symbols_cache
        
        # Try to load from cache file
        if not force_refresh:
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    self.symbols_cache = cached_data
                    return self.symbols_cache
            except:
                pass
        
        # Fetch fresh data
        all_symbols = []
        
        # Get NASDAQ symbols
        nasdaq_symbols = self.fetch_nasdaq_symbols()
        all_symbols.extend(nasdaq_symbols)
        
        # Get NYSE symbols  
        nyse_symbols = self.fetch_nyse_symbols()
        all_symbols.extend(nyse_symbols)
        
        # Get international symbols
        international_symbols = self.fetch_international_symbols()
        all_symbols.extend(international_symbols)
        
        # Remove duplicates
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            if symbol['symbol'] not in seen:
                seen.add(symbol['symbol'])
                unique_symbols.append(symbol)
        
        self.symbols_cache = unique_symbols
        
        # Save to cache file
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(unique_symbols, f)
        except:
            pass
        
        return unique_symbols
    
    def search_symbols(self, query: str, limit: int = 50) -> List[Dict]:
        """Search symbols by query"""
        if not query:
            return []
        
        symbols = self.get_all_symbols()
        query = query.upper()
        
        matches = []
        
        # Exact symbol matches first
        for symbol in symbols:
            if symbol['symbol'] == query:
                matches.append(symbol)
        
        # Symbol starts with query
        for symbol in symbols:
            if symbol['symbol'].startswith(query) and symbol not in matches:
                matches.append(symbol)
        
        # Symbol contains query
        for symbol in symbols:
            if query in symbol['symbol'] and symbol not in matches:
                matches.append(symbol)
        
        # Company name contains query
        for symbol in symbols:
            if query in symbol['name'].upper() and symbol not in matches:
                matches.append(symbol)
        
        return matches[:limit]
    
    def get_symbols_by_sector(self, sector: str) -> List[Dict]:
        """Get symbols filtered by sector"""
        symbols = self.get_all_symbols()
        return [s for s in symbols if s.get('sector', '').lower() == sector.lower()]
    
    def get_symbol_count(self) -> int:
        """Get total number of available symbols"""
        return len(self.get_all_symbols())