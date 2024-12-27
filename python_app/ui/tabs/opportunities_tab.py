import streamlit as st
import pandas as pd
from typing import List
from models.opportunities import Opportunity
from models.allocation.optimizer import AllocationOptimizer
from utils.formatting import color_apr, format_currency, format_grt, format_percentage
from api.graph_api import get_account_balance

def render_opportunities_tab(
    opportunities: List[Opportunity],
    grt_price: float,
    wallet_address: str
) -> None:
    """Render the Find Opportunities tab content."""
    st.subheader("Find Opportunities")
    
    # Get account balance
    try:
        available_grt = get_account_balance(wallet_address)
        st.write(f"Available GRT Balance: {format_grt(available_grt)}")
        st.write(f"Value in USD: {format_currency(available_grt * grt_price)}")
    except Exception as e:
        st.error(f"Error fetching account balance: {str(e)}")
        return
    
    if available_grt <= 0:
        st.warning("No GRT available for allocation.")
        return
    
    # Initialize optimizer
    optimizer = AllocationOptimizer(opportunities, grt_price)
    
    # Calculate optimal allocation
    try:
        result = optimizer.optimize_allocation(available_grt)
        
        # Display allocation summary
        st.write(f"Optimal allocation of {format_grt(available_grt)} across subgraphs to maximize rewards.")
        
        # Prepare data for display
        data = []
        for opp in opportunities:
            allocated_amount = result.allocations.get(opp.ipfs_hash, 0)
            if allocated_amount > 0:
                # Calculate metrics for this allocation
                signal_amount_after = opp.signal_amount + allocated_amount
                signalled_tokens_after = opp.signalled_tokens + allocated_amount
                portion_owned_after = signal_amount_after / signalled_tokens_after
                estimated_earnings_after = opp.curator_share * portion_owned_after
                apr_after = (estimated_earnings_after / (signal_amount_after * grt_price)) * 100

                data.append({
                    'Current Signal (GRT)': round(opp.signal_amount, 2),
                    'Allocated Amount (GRT)': round(allocated_amount, 2),
                    'Total Signal After (GRT)': round(signal_amount_after, 2),
                    'Current APR (%)': round(opp.apr, 2),
                    'APR After (%)': round(apr_after, 2),
                    'Est. Annual Earnings ($)': round(estimated_earnings_after, 2),
                    'Weekly Queries': opp.weekly_queries,
                    'IPFS Hash': opp.ipfs_hash
                })

        # Display opportunities table
        if data:
            df = pd.DataFrame(data)
            styled_df = df.style.map(color_apr, subset=['Current APR (%)', 'APR After (%)'])
            st.table(styled_df)

            # Display results summary
            st.subheader("Allocation Results")
            st.write(f"Total GRT to Allocate: {format_grt(result.total_allocated)}")
            st.write(f"Total Value to Allocate: {format_currency(result.total_allocated * grt_price)}")
            
            st.write("Estimated Annual Earnings:")
            st.write(f"- Per Day: {format_currency(result.expected_earnings / 365)}")
            st.write(f"- Per Week: {format_currency(result.expected_earnings / 52)}")
            st.write(f"- Per Month: {format_currency(result.expected_earnings / 12)}")
            st.write(f"- Per Year: {format_currency(result.expected_earnings)}")
            
            st.write(f"Expected Overall APR: {format_percentage(result.expected_apr)}")
            
            # Add allocation instructions
            st.subheader("Allocation Instructions")
            st.write("""
            To implement this allocation:
            1. Visit The Graph Explorer (https://thegraph.com/explorer)
            2. Search for each subgraph using its IPFS hash
            3. Click "Signal" and enter the allocated amount
            4. Confirm the transaction in your wallet
            """)
        else:
            st.warning("No optimal allocations found.")
            
    except Exception as e:
        st.error(f"Error calculating optimal allocation: {str(e)}")
