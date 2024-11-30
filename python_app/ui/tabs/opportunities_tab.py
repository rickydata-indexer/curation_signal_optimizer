import streamlit as st
import pandas as pd
from typing import List
from models.opportunities import Opportunity, calculate_signal_distribution
from utils.formatting import color_apr, format_currency, format_grt, format_percentage

def render_opportunities_tab(
    opportunities: List[Opportunity],
    grt_price: float
) -> None:
    """Render the Find Opportunities tab content."""
    st.subheader("Find Opportunities")
    
    # User inputs
    total_signal_to_add = st.number_input(
        "Total signal amount to add (GRT)",
        value=10000,
        min_value=0
    )
    num_subgraphs = st.number_input(
        "Number of subgraphs to allocate across",
        value=5,
        min_value=1
    )

    # Calculate signal distribution
    top_opportunities = opportunities[:num_subgraphs]
    allocations = calculate_signal_distribution(
        top_opportunities,
        total_signal_to_add,
        grt_price
    )

    # Prepare data for display
    data = []
    total_estimated_earnings_after = 0
    total_allocated_signal = 0

    for opp in top_opportunities:
        ipfs_hash = opp.ipfs_hash
        signal_amount_before = opp.signal_amount
        signalled_tokens_before = opp.signalled_tokens
        curator_share = opp.curator_share
        weekly_queries = opp.weekly_queries

        apr_before = opp.apr

        allocated_amount = allocations[ipfs_hash]
        total_allocated_signal += allocated_amount

        # After adding tokens
        signal_amount_after = signal_amount_before + allocated_amount
        signalled_tokens_after = signalled_tokens_before + allocated_amount
        portion_owned_after = signal_amount_after / signalled_tokens_after
        estimated_earnings_after = curator_share * portion_owned_after
        apr_after = (estimated_earnings_after / (signal_amount_after * grt_price)) * 100 if allocated_amount > 0 else None

        total_estimated_earnings_after += estimated_earnings_after

        data.append({
            'Signal Before (GRT)': round(signal_amount_before, 2) if signal_amount_before is not None else '-',
            'Signal After (GRT)': round(signal_amount_after, 2) if signal_amount_after is not None else '-',
            'APR Before (%)': round(apr_before, 2) if apr_before is not None else '-',
            'APR After (%)': round(apr_after, 2) if apr_after is not None else '-',
            'Earnings After ($)': round(estimated_earnings_after, 2) if estimated_earnings_after is not None else '-',
            'Allocated Signal (GRT)': round(allocated_amount, 2) if allocated_amount is not None else '-',
            'Weekly Queries': weekly_queries if weekly_queries is not None else '-',
            'IPFS Hash': ipfs_hash
        })

    # Display allocation summary
    st.write(f"Signaling {format_grt(total_signal_to_add)} across {num_subgraphs} subgraphs to maximize rewards.")

    # Display opportunities table
    df = pd.DataFrame(data)
    styled_df = df.style.map(color_apr, subset=['APR Before (%)', 'APR After (%)'])
    st.table(styled_df)

    # Display results summary
    st.subheader("Signal Results")
    st.write(f"Total GRT Signaled: {format_grt(total_allocated_signal)}")
    st.write(f"Total Value of Signaled GRT: {format_currency(total_allocated_signal * grt_price)}")
    
    st.write("Estimated Earnings:")
    st.write(f"- Per Day: {format_currency(total_estimated_earnings_after / 365)}")
    st.write(f"- Per Week: {format_currency(total_estimated_earnings_after / 52)}")
    st.write(f"- Per Month: {format_currency(total_estimated_earnings_after / 12)}")
    st.write(f"- Per Year: {format_currency(total_estimated_earnings_after)}")
    
    # Calculate and display weighted APR
    weighted_apr = sum(
        row['APR After (%)'] * row['Allocated Signal (GRT)']
        for row in data
        if row['APR After (%)'] != '-' and row['Allocated Signal (GRT)'] != '-'
    ) / total_allocated_signal if total_allocated_signal > 0 else 0
    
    st.write(f"Overall APR: {format_percentage(weighted_apr)}")
