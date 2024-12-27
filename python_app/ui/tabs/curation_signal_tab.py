import streamlit as st
import pandas as pd
from typing import List
from models.signals import UserOpportunity
from utils.formatting import color_apr, format_currency, format_grt, format_percentage

def render_curation_signal_tab(
    user_opportunities: List[UserOpportunity],
    grt_price: float
) -> None:
    """Render the Current Curation Signal tab content."""
    st.subheader("Your Current Curation Signal")
    
    # Calculate total metrics
    total_signal = sum(opp.user_signal for opp in user_opportunities)
    total_earnings = sum(opp.estimated_earnings for opp in user_opportunities)
    overall_apr = (total_earnings / (total_signal * grt_price)) * 100 if total_signal > 0 and grt_price > 0 else 0
    
    # Display summary metrics
    st.write(f"Total Curated Signal: {format_grt(total_signal)}")
    st.write(f"Total Value of Curated Signal: {format_currency(total_signal * grt_price)}")
    st.write(f"Estimated Annual Earnings: {format_currency(total_earnings)}")
    st.write(f"Overall APR: {format_percentage(overall_apr)}")
    
    # Prepare data for table
    user_data = []
    for opp in user_opportunities:
        user_data.append({
            'Your Signal (GRT)': round(opp.user_signal, 2) if opp.user_signal is not None else '-',
            'Total Signal (GRT)': round(opp.total_signal, 2) if opp.total_signal is not None else '-',
            'Portion Owned': f"{opp.portion_owned:.2%}" if opp.portion_owned is not None else '-',
            'Estimated Annual Earnings ($)': round(opp.estimated_earnings, 2) if opp.estimated_earnings is not None else '-',
            'APR (%)': round(opp.apr, 2) if opp.apr is not None else '-',
            'Weekly Queries': opp.weekly_queries if opp.weekly_queries is not None else '-',
            'IPFS Hash': opp.ipfs_hash
        })
    
    # Create and display table
    user_df = pd.DataFrame(user_data)
    styled_user_df = user_df.style.map(color_apr, subset=['APR (%)'])
    st.table(styled_user_df)
