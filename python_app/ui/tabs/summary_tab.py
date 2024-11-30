import streamlit as st
import pandas as pd
from typing import List, Dict
from models.signals import UserOpportunity
from utils.formatting import color_apr, format_currency, format_grt, format_percentage

def render_summary_tab(
    wallet_address: str,
    grt_price: float,
    user_signals: Dict[str, float],
    user_opportunities: List[UserOpportunity]
) -> None:
    """Render the Summary tab content."""
    st.subheader("Summary")
    st.write(f"Current GRT Price: {format_currency(grt_price)}")

    if not user_signals:
        st.warning("No curation signals found for this wallet address.")
        return

    if not user_opportunities:
        st.warning("No opportunities found for your current curation signals.")
        return

    # Calculate summary metrics
    total_signal = sum(opp.user_signal for opp in user_opportunities)
    total_earnings = sum(opp.estimated_earnings for opp in user_opportunities)
    overall_apr = (total_earnings / (total_signal * grt_price)) * 100 if total_signal > 0 and grt_price > 0 else 0

    # Display summary metrics
    st.write(f"Total Signal: {format_grt(total_signal)}")
    st.write(f"Overall APR: {format_percentage(overall_apr)}")
    
    # Display earnings breakdown
    st.write("Estimated Earnings:")
    st.write(f"- Daily: {format_currency(total_earnings / 365)}")
    st.write(f"- Weekly: {format_currency(total_earnings / 52)}")
    st.write(f"- Monthly: {format_currency(total_earnings / 12)}")
    st.write(f"- Yearly: {format_currency(total_earnings)}")

    # Display low performing signals
    st.subheader("Low Performing Signals (APR < 1%)")
    low_performing = [opp for opp in user_opportunities if opp.apr < 1]
    
    if low_performing:
        low_df = pd.DataFrame([{
            'Signal (GRT)': round(opp.user_signal, 2),
            'APR (%)': round(opp.apr, 2),
            'IPFS Hash': opp.ipfs_hash
        } for opp in low_performing])
        
        st.table(low_df.style.map(color_apr, subset=['APR (%)']))
    else:
        st.write("No signals with APR below 1%")
