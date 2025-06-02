import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.data_fetcher import DataFetcher
from utils.portfolio_manager import PortfolioManager
from auth import require_auth

st.set_page_config(page_title="Stocks", page_icon="📈", layout="wide")

@require_auth
def main():
    # Initialize components
    if 'data_fetcher' not in st.session_state:
        st.session_state.data_fetcher = DataFetcher()

    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = PortfolioManager()

    data_fetcher = st.session_state.data_fetcher
    portfolio_manager = st.session_state.portfolio_manager

    st.title("📈 Stocks Portfolio")

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

    # Add new stock position
    st.subheader("Add New Stock")

    col1, col2, col3 = st.columns(3)

    with col1:
        stock_symbol = st.text_input("Stock Symbol", placeholder="AAPL").upper()

    with col2:
        num_shares = st.number_input("Number of Shares", min_value=0.0001, step=1.0, format="%.4f")

    with col3:
        # Get current market price if symbol is valid
        custom_price = None
        if stock_symbol:
            quote = data_fetcher.get_real_time_quote(stock_symbol)
            if quote:
                market_price = quote['price']
                st.write(f"Current Market Price: ${market_price:.2f}")
                use_market_price = st.checkbox("Use Market Price", value=True)

                if use_market_price:
                    price_per_share = market_price
                    st.write(f"Using: ${price_per_share:.2f}")
                else:
                    custom_price = st.number_input("Custom Price per Share", min_value=0.01, value=market_price, step=0.01, format="%.2f")
                    price_per_share = custom_price
            else:
                price_per_share = st.number_input("Price per Share", min_value=0.01, step=0.01, format="%.2f")
        else:
            price_per_share = st.number_input("Price per Share", min_value=0.01, step=0.01, format="%.2f")

    # Calculate total cost
    if num_shares > 0 and price_per_share > 0:
        total_cost = num_shares * price_per_share
        st.write(f"**Total Cost: ${total_cost:,.2f}**")

    if st.button("Add to Portfolio", type="primary"):
        if stock_symbol and num_shares > 0 and price_per_share > 0:
            if data_fetcher.validate_symbol(stock_symbol):
                try:
                    portfolio_manager.add_transaction(
                        stock_symbol, "buy", num_shares, price_per_share
                    )
                    st.success(f"Added {num_shares} shares of {stock_symbol} at ${price_per_share:.2f}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding position: {str(e)}")
            else:
                st.error(f"Invalid stock symbol: {stock_symbol}")
        else:
            st.error("Please fill in all fields with valid values")

    # Current Holdings
    if portfolio_data['holdings']:
        st.subheader("Current Holdings")

        # Holdings table
        holdings_df = pd.DataFrame(portfolio_data['holdings'])

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

            # Rename columns for display
            display_df = display_df.rename(columns={
                'symbol': 'Symbol',
                'shares': 'Shares',
                'avg_cost': 'Avg Cost',
                'current_price': 'Current Price',
                'cost_basis': 'Total Cost',
                'current_value': 'Current Value',
                'gain_loss': 'Gain/Loss ($)',
                'gain_loss_pct': 'Gain/Loss (%)'
            })

            # Display with color coding
            st.dataframe(
                display_df[['Symbol', 'Shares', 'Avg Cost', 'Current Price', 'Total Cost', 'Current Value', 'Gain/Loss ($)', 'Gain/Loss (%)']],
                use_container_width=True
            )

            # Portfolio allocation chart
            st.subheader("Portfolio Allocation")

            fig = px.pie(
                holdings_df,
                values='current_value',
                names='symbol',
                title="Portfolio Allocation by Value"
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)

            st.plotly_chart(fig, use_container_width=True)

            # Manage individual holdings
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
                    st.write("**Sell Shares:**")

                    sell_shares = st.number_input("Shares to Sell", min_value=0.0001, max_value=holding_data['shares'], step=0.1, format="%.4f")
                    sell_price = st.number_input("Sell Price per Share", min_value=0.01, value=holding_data['current_price'], step=0.01, format="%.2f")

                    if st.button("Sell Shares"):
                        try:
                            portfolio_manager.add_transaction(
                                selected_holding, "sell", sell_shares, sell_price
                            )
                            st.success(f"Sold {sell_shares} shares of {selected_holding}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error selling shares: {str(e)}")

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
                file_name=f"stock_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No transactions recorded yet. Add your first stock above!")

main()