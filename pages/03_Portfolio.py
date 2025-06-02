import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from utils.data_fetcher import DataFetcher
from utils.portfolio_manager import PortfolioManager

st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")

# Initialize components
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = DataFetcher()

if 'portfolio_manager' not in st.session_state:
    st.session_state.portfolio_manager = PortfolioManager()

data_fetcher = st.session_state.data_fetcher
portfolio_manager = st.session_state.portfolio_manager

st.title("💼 Portfolio Management")

# Portfolio overview
portfolio_data = portfolio_manager.get_portfolio_value(data_fetcher)

# Display portfolio summary
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Value",
        f"${portfolio_data['total_value']:,.2f}",
        f"${portfolio_data['total_gain_loss']:+,.2f}"
    )

with col2:
    st.metric(
        "Total Cost",
        f"${portfolio_data['total_cost']:,.2f}"
    )

with col3:
    st.metric(
        "Total Gain/Loss",
        f"${portfolio_data['total_gain_loss']:+,.2f}",
        f"{portfolio_data['total_gain_loss_pct']:+.2f}%"
    )

with col4:
    st.metric(
        "Number of Holdings",
        len(portfolio_data['holdings'])
    )

# Portfolio allocation chart
if portfolio_data['holdings']:
    st.subheader("Portfolio Allocation")
    
    # Create pie chart for allocation
    holdings_df = pd.DataFrame(portfolio_data['holdings'])
    
    fig = px.pie(
        holdings_df,
        values='current_value',
        names='symbol',
        title="Portfolio Allocation by Value"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Holdings table
    st.subheader("Current Holdings")
    
    if not holdings_df.empty:
        # Format the dataframe for display
        display_df = holdings_df.copy()
        display_df['shares'] = display_df['shares'].round(4)
        display_df['avg_cost'] = display_df['avg_cost'].round(2)
        display_df['current_price'] = display_df['current_price'].round(2)
        display_df['cost_basis'] = display_df['cost_basis'].round(2)
        display_df['current_value'] = display_df['current_value'].round(2)
        display_df['gain_loss'] = display_df['gain_loss'].round(2)
        display_df['gain_loss_pct'] = display_df['gain_loss_pct'].round(2)
        display_df['day_change_pct'] = display_df['day_change_pct'].round(2)
        
        # Rename columns for display
        display_df = display_df.rename(columns={
            'symbol': 'Symbol',
            'shares': 'Shares',
            'avg_cost': 'Avg Cost',
            'current_price': 'Current Price',
            'cost_basis': 'Cost Basis',
            'current_value': 'Current Value',
            'gain_loss': 'Gain/Loss ($)',
            'gain_loss_pct': 'Gain/Loss (%)',
            'day_change_pct': 'Day Change (%)'
        })
        
        # Display with color coding
        st.dataframe(
            display_df[['Symbol', 'Shares', 'Avg Cost', 'Current Price', 'Cost Basis', 'Current Value', 'Gain/Loss ($)', 'Gain/Loss (%)', 'Day Change (%)']],
            use_container_width=True
        )
        
        # Individual holding actions
        st.subheader("Manage Holdings")
        
        selected_holding = st.selectbox(
            "Select holding to manage:",
            [''] + [holding['symbol'] for holding in portfolio_data['holdings']]
        )
        
        if selected_holding:
            holding_data = next(h for h in portfolio_data['holdings'] if h['symbol'] == selected_holding)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**{selected_holding} Holdings:**")
                st.write(f"Shares: {holding_data['shares']}")
                st.write(f"Average Cost: ${holding_data['avg_cost']:.2f}")
                st.write(f"Current Price: ${holding_data['current_price']:.2f}")
                st.write(f"Total Value: ${holding_data['current_value']:.2f}")
                
                if st.button(f"Remove {selected_holding} from Portfolio", type="secondary"):
                    portfolio_manager.remove_holding(selected_holding)
                    st.success(f"Removed {selected_holding} from portfolio")
                    st.rerun()
            
            with col2:
                st.write("**Add Transaction:**")
                
                action = st.selectbox("Action", ["Buy", "Sell"])
                shares = st.number_input("Shares", min_value=0.0001, step=0.1, format="%.4f")
                price = st.number_input("Price per Share", min_value=0.01, step=0.01, format="%.2f")
                
                if st.button("Add Transaction"):
                    try:
                        portfolio_manager.add_transaction(
                            selected_holding, action.lower(), shares, price
                        )
                        st.success(f"Added {action.lower()} transaction for {selected_holding}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding transaction: {str(e)}")

# Add new position
st.subheader("Add New Position")

col1, col2, col3, col4 = st.columns(4)

with col1:
    new_symbol = st.text_input("Stock Symbol", placeholder="AAPL").upper()

with col2:
    new_shares = st.number_input("Shares", min_value=0.0001, step=0.1, format="%.4f")

with col3:
    new_price = st.number_input("Purchase Price", min_value=0.01, step=0.01, format="%.2f")

with col4:
    st.write("")  # Spacer
    st.write("")  # Spacer
    if st.button("Add Position", type="primary"):
        if new_symbol and new_shares > 0 and new_price > 0:
            if data_fetcher.validate_symbol(new_symbol):
                try:
                    portfolio_manager.add_transaction(
                        new_symbol, "buy", new_shares, new_price
                    )
                    st.success(f"Added {new_shares} shares of {new_symbol} at ${new_price:.2f}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding position: {str(e)}")
            else:
                st.error(f"Invalid stock symbol: {new_symbol}")
        else:
            st.error("Please fill in all fields with valid values")

# Portfolio performance chart
if portfolio_data['holdings']:
    st.subheader("Portfolio Performance")
    
    period = st.selectbox(
        "Performance Period",
        ["1mo", "3mo", "6mo", "1y"],
        index=1
    )
    
    try:
        performance_data = portfolio_manager.get_portfolio_performance(data_fetcher, period)
        
        if performance_data:
            fig = go.Figure()
            
            # Individual holdings
            for symbol in performance_data['symbols']:
                if symbol in performance_data['data'].columns:
                    fig.add_trace(
                        go.Scatter(
                            x=performance_data['data'].index,
                            y=performance_data['data'][symbol],
                            mode='lines',
                            name=symbol,
                            line=dict(width=1),
                            opacity=0.7
                        )
                    )
            
            # Total portfolio
            fig.add_trace(
                go.Scatter(
                    x=performance_data['data'].index,
                    y=performance_data['total_series'],
                    mode='lines',
                    name='Total Portfolio',
                    line=dict(width=3, color='black')
                )
            )
            
            fig.update_layout(
                title=f"Portfolio Performance ({period})",
                xaxis_title="Date",
                yaxis_title="Value ($)",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough historical data to show performance chart")
    
    except Exception as e:
        st.error(f"Error loading performance data: {str(e)}")

# Transaction history
st.subheader("Transaction History")

transactions_df = portfolio_manager.get_transactions_df()

if not transactions_df.empty:
    # Format for display
    display_transactions = transactions_df.copy()
    display_transactions['date'] = pd.to_datetime(display_transactions['date']).dt.strftime('%Y-%m-%d %H:%M')
    display_transactions['total'] = display_transactions['total'].round(2)
    display_transactions['price'] = display_transactions['price'].round(2)
    
    st.dataframe(
        display_transactions[['date', 'symbol', 'action', 'shares', 'price', 'total']],
        use_container_width=True
    )
    
    # Export transactions
    if st.button("Export Transaction History"):
        csv = transactions_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"portfolio_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
else:
    st.info("No transactions recorded yet. Add your first position above!")

# Portfolio import/export
st.subheader("Portfolio Data Management")

col1, col2 = st.columns(2)

with col1:
    st.write("**Export Portfolio**")
    if st.button("Export Portfolio Data"):
        portfolio_json = portfolio_manager.export_portfolio()
        st.download_button(
            label="Download Portfolio JSON",
            data=portfolio_json,
            file_name=f"portfolio_backup_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col2:
    st.write("**Import Portfolio**")
    uploaded_file = st.file_uploader("Choose portfolio JSON file", type="json")
    
    if uploaded_file is not None:
        try:
            portfolio_json = uploaded_file.read().decode("utf-8")
            if st.button("Import Portfolio"):
                if portfolio_manager.import_portfolio(portfolio_json):
                    st.success("Portfolio imported successfully!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# Clear portfolio option
with st.expander("⚠️ Danger Zone"):
    st.warning("This action cannot be undone!")
    if st.button("Clear All Portfolio Data", type="secondary"):
        if st.session_state.get('confirm_clear', False):
            portfolio_manager.clear_portfolio()
            st.success("Portfolio cleared!")
            st.session_state.confirm_clear = False
            st.rerun()
        else:
            st.session_state.confirm_clear = True
            st.error("Click again to confirm clearing all portfolio data")
