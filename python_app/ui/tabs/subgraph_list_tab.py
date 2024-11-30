import streamlit as st
import pandas as pd
from typing import List
from models.opportunities import Opportunity
from utils.formatting import color_apr, format_grt, format_percentage

def render_subgraph_list_tab(opportunities: List[Opportunity]) -> None:
    """Render the Full Subgraph List tab content."""
    st.subheader("Full Subgraph List")
    
    # Prepare data for table
    data = []
    for opp in opportunities:
        data.append({
            'Signal (GRT)': round(opp.signal_amount, 2),
            'Total Signal (GRT)': round(opp.signalled_tokens, 2),
            'APR (%)': round(opp.apr, 2),
            'Weekly Queries': opp.weekly_queries,
            'IPFS Hash': opp.ipfs_hash
        })
    
    # Create and display table
    df = pd.DataFrame(data)
    styled_df = df.style.map(color_apr, subset=['APR (%)'])
    st.table(styled_df)
    
    # Add download button
    st.download_button(
        label="Download Full Subgraph List",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='full_subgraph_list.csv',
        mime='text/csv'
    )
