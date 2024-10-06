import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
from scipy.optimize import minimize
import statistics
import sys
import subprocess
import importlib

# GraphQL query to get subgraph deployment data
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_subgraph_deployments():
    url = "https://gateway.thegraph.com/api/040d2183b97fb279ac2cb8fb2c78beae/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp"
    query_template = '''
    {
      subgraphDeployments(first: 1000, where: {id_gt: "%s"}, orderBy: id, orderDirection: asc) {
        id
        ipfsHash
        signalAmount
        signalledTokens
        stakedTokens
        queryFeesAmount
        queryFeeRebates
      }
    }
    '''
    
    all_deployments = []
    last_id = ""
    
    while True:
        query = query_template % last_id
        response = requests.post(url, json={'query': query})
        if response.status_code != 200:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")
        
        data = response.json()
        deployments = data['data']['subgraphDeployments']
        
        if not deployments:
            break
        
        all_deployments.extend(deployments)
        last_id = deployments[-1]['id']
    
    return all_deployments

# Function to process CSV files and aggregate query fees and counts
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def process_csv_files(directory):
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    query_fees = {}
    query_counts = {}

    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            df = pd.read_csv(os.path.join(directory, filename))
            df['end_epoch'] = pd.to_datetime(df['end_epoch'])

            # Filter data for the last week
            df_week = df[df['end_epoch'] > week_ago]

            # Group by subgraph deployment and sum query fees and counts
            grouped_fees = df_week.groupby('subgraph_deployment_ipfs_hash')['total_query_fees'].sum()
            grouped_counts = df_week.groupby('subgraph_deployment_ipfs_hash')['query_count'].sum()

            for ipfs_hash, fees in grouped_fees.items():
                if ipfs_hash in query_fees:
                    query_fees[ipfs_hash] += fees
                else:
                    query_fees[ipfs_hash] = fees

            for ipfs_hash, count in grouped_counts.items():
                if ipfs_hash in query_counts:
                    query_counts[ipfs_hash] += count
                else:
                    query_counts[ipfs_hash] = count

    return query_fees, query_counts

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_grt_price():
    url = "https://gateway.thegraph.com/api/040d2183b97fb279ac2cb8fb2c78beae/subgraphs/id/4RTrnxLZ4H8EBdpAQTcVc7LQY9kk85WNLyVzg5iXFQCH"
    query = """
    {
      assetPairs(
        first: 1
        where: {asset: "0xc944e90c64b2c07662a292be6244bdf05cda44a7", comparedAsset: "0x0000000000000000000000000000000000000348"}
      ) {
        currentPrice
      }
    }
    """
    response = requests.post(url, json={'query': query})
    data = response.json()
    return float(data['data']['assetPairs'][0]['currentPrice'])

def calculate_opportunities(deployments, query_fees, query_counts, grt_price):
    opportunities = []

    for deployment in deployments:
        ipfs_hash = deployment['ipfsHash']
        signal_amount = float(deployment['signalAmount']) / 1e18  # Convert wei to GRT
        signalled_tokens = float(deployment['signalledTokens']) / 1e18  # Convert wei to GRT

        if ipfs_hash in query_counts:
            weekly_queries = query_counts[ipfs_hash]
            annual_queries = weekly_queries * 52  # Annualize the queries

            # Calculate total earnings based on $4 per 100,000 queries
            total_earnings = (annual_queries / 100000) * 4

            # Calculate the curator's share (10% of total earnings)
            curator_share = total_earnings * 0.1

            # Calculate the portion owned by the curator
            if signalled_tokens > 0:
                portion_owned = signal_amount / signalled_tokens
            else:
                portion_owned = 0

            # Calculate estimated annual earnings for this curator
            estimated_earnings = curator_share * portion_owned

            # Calculate APR using GRT price
            if signal_amount > 0:
                apr = (estimated_earnings / (signal_amount * grt_price)) * 100
            else:
                apr = 0

            opportunities.append({
                'ipfs_hash': ipfs_hash,
                'signal_amount': signal_amount,
                'signalled_tokens': signalled_tokens,
                'annual_queries': annual_queries,
                'total_earnings': total_earnings,
                'curator_share': curator_share,
                'estimated_earnings': estimated_earnings,
                'apr': apr,
                'weekly_queries': weekly_queries
            })

    # Filter out subgraphs with zero signal amounts
    opportunities = [opp for opp in opportunities if opp['signal_amount'] > 0]

    # Sort opportunities by APR in descending order
    return sorted(opportunities, key=lambda x: x['apr'], reverse=True)

def color_apr(val):
    if val is None or val == '-':
        return 'color: gray'
    try:
        val = float(val)
        if val > 5:
            color = 'green'
        elif val < 1:
            color = 'red'
        else:
            color = 'black'
        return f'color: {color}'
    except ValueError:
        return 'color: gray'

def display_full_subgraph_list(opportunities):
    st.subheader("Full Subgraph List")
    data = []
    for opp in opportunities:
        data.append({
            'Signal (GRT)': round(opp['signal_amount'], 2),
            'Total Signal (GRT)': round(opp['signalled_tokens'], 2),
            'APR (%)': round(opp['apr'], 2),
            'Weekly Queries': opp['weekly_queries'],
            'IPFS Hash': opp['ipfs_hash']
        })
    df = pd.DataFrame(data)
    styled_df = df.style.map(color_apr, subset=['APR (%)'])
    st.table(styled_df)
    st.download_button(
        label="Download Full Subgraph List",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='full_subgraph_list.csv',
        mime='text/csv'
    )

def main():
    st.title("Curation Signal Allocation Optimizer")
    st.write("You can only access this data if you are actively delegating to this indexer: https://thegraph.com/explorer/profile/0x74dbb201ecc0b16934e68377bc13013883d9417b")

    # Data Retrieval and Processing
    deployments = get_subgraph_deployments()
    query_fees, query_counts = process_csv_files('/root/graphprotocol-mainnet-docker/python_data/hourly_query_volume/')
    grt_price = get_grt_price()
    opportunities = calculate_opportunities(deployments, query_fees, query_counts, grt_price)

    # Define Tabs
    tab_labels = ["Summary", "Find Opportunities", "Full Subgraph List"]
    tabs = st.tabs(tab_labels)

    with tabs[0]:  # Summary tab
        st.subheader("Summary")
        st.write(f"Current GRT Price: ${grt_price:.2f}")

    with tabs[1]:  # Find Opportunities tab
        st.subheader("Find Opportunities")
        
        # User Inputs specific to this tab
        total_signal_to_add = st.number_input("Total signal amount to add (GRT)", value=10000, min_value=0)
        num_subgraphs = st.number_input("Number of subgraphs to allocate across", value=5, min_value=1)

        # Display summary stats
        st.write(f"Signaling {total_signal_to_add:,.2f} GRT across {num_subgraphs} subgraphs to maximize rewards.")

    with tabs[2]:  # Full Subgraph List tab
        display_full_subgraph_list(opportunities)

if __name__ == "__main__":
    main()
