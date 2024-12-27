import streamlit as st
from utils.config import DEFAULT_WALLET
from api.graph_api import get_subgraph_deployments, get_grt_price, get_user_curation_signal
from api.supabase_api import process_query_data
from models.opportunities import calculate_opportunities
from models.signals import calculate_user_opportunities
from ui.tabs.summary_tab import render_summary_tab
from ui.tabs.curation_signal_tab import render_curation_signal_tab
from ui.tabs.opportunities_tab import render_opportunities_tab
from ui.tabs.subgraph_list_tab import render_subgraph_list_tab

def main():
    """Main application entry point."""
    st.title("Curation Signal Allocation Optimizer")
    st.write("This app helps you allocate your curation signal across subgraphs to maximize your APR.")

    # Get wallet address input first, so it's available for all tabs
    wallet_address = st.text_input("Enter your wallet address", value=DEFAULT_WALLET).lower()

    # Define Tabs
    tab_labels = ["Summary", "Your Current Curation Signal", "Find Opportunities", "Full Subgraph List"]
    tabs = st.tabs(tab_labels)

    # Data Retrieval and Processing
    deployments = get_subgraph_deployments()
    query_fees, query_counts = process_query_data()
    grt_price = get_grt_price()
    opportunities = calculate_opportunities(deployments, query_fees, query_counts, grt_price)

    user_signals = get_user_curation_signal(wallet_address)
    if not user_signals:
        st.warning("No curation signals found for this wallet address.")
        return

    user_opportunities = calculate_user_opportunities(user_signals, opportunities, grt_price)
    if not user_opportunities:
        st.warning("No opportunities found for your current curation signals.")
        return

    # Render each tab
    with tabs[0]:  # Summary tab
        render_summary_tab(wallet_address, grt_price, user_signals, user_opportunities)

    if wallet_address:
        with tabs[1]:  # Your Current Curation Signal tab
            render_curation_signal_tab(user_opportunities, grt_price)
        
        with tabs[2]:  # Find Opportunities tab
            render_opportunities_tab(opportunities, grt_price, wallet_address)

        with tabs[3]:  # Full Subgraph List tab
            render_subgraph_list_tab(opportunities)

if __name__ == "__main__":
    main()
