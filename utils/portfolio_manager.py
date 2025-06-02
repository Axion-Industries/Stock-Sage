import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import json
from utils.data_persistence import data_persistence

class PortfolioManager:
    def __init__(self):
        self.portfolio_key = "user_portfolio"
        self.transactions_key = "user_transactions"
        
    def get_portfolio(self):
        """Get current portfolio holdings"""
        if self.portfolio_key not in st.session_state:
            st.session_state[self.portfolio_key] = {}
        return st.session_state[self.portfolio_key]
    
    def get_transactions(self):
        """Get transaction history"""
        if self.transactions_key not in st.session_state:
            st.session_state[self.transactions_key] = []
        return st.session_state[self.transactions_key]
    
    def add_transaction(self, symbol, action, shares, price, date=None):
        """
        Add a transaction to the portfolio with persistent storage
        
        Args:
            symbol (str): Stock symbol
            action (str): 'buy' or 'sell'
            shares (float): Number of shares
            price (float): Price per share
            date (datetime): Transaction date (default: now)
        """
        from auth import get_current_user
        user = get_current_user()
        if not user:
            return
            
        if date is None:
            date = datetime.now()
        
        total = shares * price
        symbol = symbol.upper()
        
        # Save transaction to database
        data_persistence.add_portfolio_transaction(user['id'], symbol, action, shares, price, total)
        
        # Update portfolio holdings
        portfolio = self.get_portfolio()
        
        if symbol not in portfolio:
            portfolio[symbol] = {
                'shares': 0,
                'avg_cost': 0,
                'total_cost': 0
            }
        
        if action.lower() == 'buy':
            # Calculate new average cost
            old_shares = portfolio[symbol]['shares']
            old_total_cost = portfolio[symbol]['total_cost']
            new_total_cost = old_total_cost + (shares * price)
            new_total_shares = old_shares + shares
            
            portfolio[symbol]['shares'] = new_total_shares
            portfolio[symbol]['total_cost'] = new_total_cost
            portfolio[symbol]['avg_cost'] = new_total_cost / new_total_shares if new_total_shares > 0 else 0
            
        elif action.lower() == 'sell':
            # Reduce shares and proportionally reduce total cost
            if portfolio[symbol]['shares'] >= shares:
                old_shares = portfolio[symbol]['shares']
                cost_per_share = portfolio[symbol]['avg_cost']
                
                portfolio[symbol]['shares'] -= shares
                portfolio[symbol]['total_cost'] -= shares * cost_per_share
                
                # Remove from portfolio if no shares left
                if portfolio[symbol]['shares'] <= 0:
                    del portfolio[symbol]
            else:
                raise ValueError(f"Cannot sell {shares} shares. Only {portfolio[symbol]['shares']} available.")
        
        # Save updated portfolio to database
        for sym, holding in portfolio.items():
            data_persistence.save_portfolio_holding(
                user['id'], sym, holding['shares'], holding['avg_cost'], holding['total_cost']
            )
        
        st.session_state[self.portfolio_key] = portfolio
    
    def remove_holding(self, symbol):
        """Remove a holding from portfolio"""
        portfolio = self.get_portfolio()
        symbol = symbol.upper()
        if symbol in portfolio:
            del portfolio[symbol]
            st.session_state[self.portfolio_key] = portfolio
    
    def get_portfolio_value(self, data_fetcher):
        """
        Calculate current portfolio value using real-time data
        
        Args:
            data_fetcher: DataFetcher instance
            
        Returns:
            dict: Portfolio valuation data
        """
        portfolio = self.get_portfolio()
        if not portfolio:
            return {
                'total_value': 0,
                'total_cost': 0,
                'total_gain_loss': 0,
                'total_gain_loss_pct': 0,
                'holdings': []
            }
        
        holdings = []
        total_value = 0
        total_cost = 0
        
        for symbol, holding in portfolio.items():
            try:
                # Get current price
                quote = data_fetcher.get_real_time_quote(symbol)
                if quote:
                    current_price = quote['price']
                    shares = holding['shares']
                    avg_cost = holding['avg_cost']
                    cost_basis = holding['total_cost']
                    
                    current_value = shares * current_price
                    gain_loss = current_value - cost_basis
                    gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0
                    
                    holdings.append({
                        'symbol': symbol,
                        'shares': shares,
                        'avg_cost': avg_cost,
                        'current_price': current_price,
                        'cost_basis': cost_basis,
                        'current_value': current_value,
                        'gain_loss': gain_loss,
                        'gain_loss_pct': gain_loss_pct,
                        'day_change': quote.get('change', 0),
                        'day_change_pct': quote.get('percent_change', 0)
                    })
                    
                    total_value += current_value
                    total_cost += cost_basis
                else:
                    # If we can't get current price, use cost basis
                    holdings.append({
                        'symbol': symbol,
                        'shares': holding['shares'],
                        'avg_cost': holding['avg_cost'],
                        'current_price': 0,
                        'cost_basis': holding['total_cost'],
                        'current_value': 0,
                        'gain_loss': 0,
                        'gain_loss_pct': 0,
                        'day_change': 0,
                        'day_change_pct': 0
                    })
                    total_cost += holding['total_cost']
                    
            except Exception as e:
                st.error(f"Error calculating value for {symbol}: {str(e)}")
                continue
        
        total_gain_loss = total_value - total_cost
        total_gain_loss_pct = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_gain_loss': total_gain_loss,
            'total_gain_loss_pct': total_gain_loss_pct,
            'holdings': holdings
        }
    
    def get_transactions_df(self):
        """Get transactions as DataFrame"""
        transactions = self.get_transactions()
        if not transactions:
            return pd.DataFrame()
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date', ascending=False)
    
    def get_portfolio_performance(self, data_fetcher, period="1mo"):
        """
        Calculate portfolio performance over time
        
        Args:
            data_fetcher: DataFetcher instance
            period (str): Time period for performance calculation
            
        Returns:
            dict: Performance data
        """
        portfolio = self.get_portfolio()
        if not portfolio:
            return None
        
        symbols = list(portfolio.keys())
        performance_data = {}
        
        for symbol in symbols:
            try:
                data = data_fetcher.get_stock_data(symbol, period)
                if not data.empty:
                    shares = portfolio[symbol]['shares']
                    performance_data[symbol] = data['Close'] * shares
            except:
                continue
        
        if not performance_data:
            return None
        
        # Create combined portfolio performance
        portfolio_df = pd.DataFrame(performance_data)
        portfolio_df['total'] = portfolio_df.sum(axis=1)
        
        return {
            'data': portfolio_df,
            'symbols': symbols,
            'total_series': portfolio_df['total']
        }
    
    def export_portfolio(self):
        """Export portfolio data as JSON"""
        portfolio_data = {
            'portfolio': self.get_portfolio(),
            'transactions': self.get_transactions(),
            'export_date': datetime.now().isoformat()
        }
        return json.dumps(portfolio_data, indent=2)
    
    def import_portfolio(self, json_data):
        """Import portfolio data from JSON"""
        try:
            data = json.loads(json_data)
            if 'portfolio' in data:
                st.session_state[self.portfolio_key] = data['portfolio']
            if 'transactions' in data:
                st.session_state[self.transactions_key] = data['transactions']
            return True
        except Exception as e:
            st.error(f"Error importing portfolio: {str(e)}")
            return False
    
    def clear_portfolio(self):
        """Clear all portfolio data"""
        st.session_state[self.portfolio_key] = {}
        st.session_state[self.transactions_key] = []
