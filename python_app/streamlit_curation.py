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
import base64
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

username = os.getenv('SUPABASE_USERNAME')
password = os.getenv('SUPABASE_PASSWORD')

default_wallet = "0x74dbb201ecc0b16934e68377bc13013883d9417b"

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

def query_supabase():
    """Get data from Supabase using pg-meta endpoint."""
    try:
        import requests
        from datetime import datetime, timedelta

        # Supabase connection details
        BASE_URL = "http://supabasekong-so4w8gock004k8kw8ck84o80.94.130.17.180.sslip.io"
        API_URL = f"{BASE_URL}/api/pg-meta/default/query"  # Using pg-meta endpoint

        # Get credentials from environment variables
        username = os.getenv('SUPABASE_USERNAME')
        password = os.getenv('SUPABASE_PASSWORD')

        # Create Basic auth header
        credentials = f"{username}:{password}"
        auth_bytes = credentials.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')

        # Headers
        headers = {
            "Authorization": f"Basic {base64_auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Get data from the last week
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()

        # SQL query
        sql_query = f"""
        SELECT 
            subgraph_deployment_ipfs_hash,
            SUM(total_query_fees) as total_query_fees,
            SUM(query_count) as query_count
        FROM qos_hourly_query_volume 
        WHERE end_epoch > '{week_ago}'
        GROUP BY subgraph_deployment_ipfs_hash
        """

        # Execute the query
        response = requests.post(
            API_URL,
            headers=headers,
            json={"query": sql_query}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error executing query: HTTP {response.status_code} - {response.text}")

    except Exception as e:
        raise Exception(f"Error: {str(e)}")

# Function to process query data from Supabase
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def process_query_data():
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    try:
        rows = query_supabase()
        
        # Initialize dictionaries
        query_fees = {}
        query_counts = {}

        # Process results
        if rows:
            for row in rows:
                ipfs_hash = row['subgraph_deployment_ipfs_hash']
                if ipfs_hash:
                    query_fees[ipfs_hash] = float(row['total_query_fees'])
                    query_counts[ipfs_hash] = int(row['query_count'])

        return query_fees, query_counts

    except Exception as e:
        st.error(f"Error querying Supabase: {str(e)}")
        return {}, {}

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

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_user_curation_signal(wallet_address):
    url = "https://gateway.thegraph.com/api/040d2183b97fb279ac2cb8fb2c78beae/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp"
    query = """
    query($wallet: String!) {
      curator(id: $wallet) {
        id
        nameSignals(first: 1000) {
          signalledTokens
          unsignalledTokens
          signal
          subgraph {
            id
            metadata {
              displayName
            }
            currentVersion {
              id
              subgraphDeployment {
                ipfsHash
                pricePerShare
                signalAmount
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "wallet": wallet_address.lower()
    }
    
    response = requests.post(url, json={'query': query, 'variables': variables})
    if response.status_code != 200:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")
    
    data = response.json()
    
    curator_data = data.get('data', {}).get('curator')
    
    user_signals = {}
    if curator_data and curator_data.get('nameSignals'):
        for signal in curator_data['nameSignals']:
            subgraph = signal.get('subgraph', {})
            current_version = subgraph.get('currentVersion', {})
            subgraph_deployment = current_version.get('subgraphDeployment', {})
            
            ipfs_hash = subgraph_deployment.get('ipfsHash')
            signal_amount = float(signal.get('signal', 0)) / 1e18
            
            if ipfs_hash:
                user_signals[ipfs_hash] = signal_amount
    
    return user_signals

def calculate_user_opportunities(user_signals, opportunities, grt_price):
    user_opportunities = []
    
    for opp in opportunities:
        ipfs_hash = opp['ipfs_hash']
        
        if ipfs_hash in user_signals:
            user_signal = user_signals[ipfs_hash]
            total_signal = opp['signalled_tokens']
            portion_owned = user_signal / total_signal if total_signal > 0 else 0
            estimated_earnings = opp['curator_share'] * portion_owned
            apr = (estimated_earnings / (user_signal * grt_price)) * 100 if user_signal > 0 else 0
            
            user_opportunities.append({
                'ipfs_hash': ipfs_hash,
                'user_signal': user_signal,
                'total_signal': total_signal,
                'portion_owned': portion_owned,
                'estimated_earnings': estimated_earnings,
                'apr': apr,
                'weekly_queries': opp['weekly_queries']
            })
    
    return sorted(user_opportunities, key=lambda x: x['apr'], reverse=True)

def calculate_optimal_allocations(opportunities, user_signals, total_signal, grt_price, num_subgraphs):
    # Adjust opportunities based on user's current allocations
    adjusted_opportunities = []
    for opp in opportunities:
        ipfs_hash = opp['ipfs_hash']
        adj_opp = opp.copy()
        if ipfs_hash in user_signals:
            user_signal = user_signals[ipfs_hash]
            adj_opp['signalled_tokens'] -= user_signal
            adj_opp['signal_amount'] = 0  # Reset signal amount for recalculation
        adjusted_opportunities.append(adj_opp)

    # Sort adjusted opportunities by APR in descending order
    adjusted_opportunities = sorted(adjusted_opportunities, key=lambda x: x['apr'], reverse=True)

    # Select top opportunities
    top_opportunities = adjusted_opportunities[:num_subgraphs]

    # Initialize allocation dictionary
    allocations = {opp['ipfs_hash']: 0 for opp in top_opportunities}
    remaining_signal = total_signal

    # Iterative allocation process
    while remaining_signal > 0:
        best_apr = -1
        best_opp = None

        for opp in top_opportunities:
            ipfs_hash = opp['ipfs_hash']
            signal_amount = opp['signal_amount'] + allocations[ipfs_hash]
            signalled_tokens = opp['signalled_tokens'] + allocations[ipfs_hash]
            
            # Calculate APR if we add 100 more tokens
            new_signal_amount = signal_amount + 100
            new_signalled_tokens = signalled_tokens + 100
            portion_owned = new_signal_amount / new_signalled_tokens
            estimated_earnings = opp['curator_share'] * portion_owned
            apr = (estimated_earnings / (new_signal_amount * grt_price)) * 100

            if apr > best_apr:
                best_apr = apr
                best_opp = opp

        # Allocate 100 tokens to the best opportunity
        if best_opp:
            allocations[best_opp['ipfs_hash']] += min(100, remaining_signal)
            remaining_signal -= 100
        else:
            break

    return allocations

def calculate_signal_distribution(opportunities, total_signal, grt_price):
    # Initialize allocation dictionary
    allocations = {opp['ipfs_hash']: 0 for opp in opportunities}
    remaining_signal = total_signal

    # Iterative allocation process
    while remaining_signal > 0:
        best_apr = -1
        best_opp = None

        for opp in opportunities:
            ipfs_hash = opp['ipfs_hash']
            signal_amount = opp['signal_amount'] + allocations[ipfs_hash]
            signalled_tokens = opp['signalled_tokens'] + allocations[ipfs_hash]
            
            # Calculate APR if we add 100 more tokens
            new_signal_amount = signal_amount + 100
            new_signalled_tokens = signalled_tokens + 100
            portion_owned = new_signal_amount / new_signalled_tokens
            estimated_earnings = opp['curator_share'] * portion_owned
            apr = (estimated_earnings / (new_signal_amount * grt_price)) * 100

            if apr > best_apr:
                best_apr = apr
                best_opp = opp

        # Allocate 100 tokens to the best opportunity
        if best_opp:
            allocations[best_opp['ipfs_hash']] += min(100, remaining_signal)
            remaining_signal -= 100
        else:
            break

    return allocations

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
    st.write("This app helps you allocate your curation signal across subgraphs to maximize your APR.")

    # Define Tabs
    tab_labels = ["Summary", "Your Current Curation Signal", "Find Opportunities", "Full Subgraph List"]
    tabs = st.tabs(tab_labels)

    # Data Retrieval and Processing
    deployments = get_subgraph_deployments()
    query_fees, query_counts = process_query_data()
    grt_price = get_grt_price()
    opportunities = calculate_opportunities(deployments, query_fees, query_counts, grt_price)

    with tabs[0]:  # Summary tab
        st.subheader("Summary")
        wallet_address = st.text_input("Enter your wallet address", value=default_wallet).lower()
        st.write(f"Current GRT Price: ${grt_price:.2f}")

        user_signals = get_user_curation_signal(wallet_address)
        if not user_signals:
            st.warning("No curation signals found for this wallet address.")
            return

        user_opportunities = calculate_user_opportunities(user_signals, opportunities, grt_price)
        if not user_opportunities:
            st.warning("No opportunities found for your current curation signals.")
            return

        total_signal = sum(opp['user_signal'] for opp in user_opportunities)
        total_earnings = sum(opp['estimated_earnings'] for opp in user_opportunities)
        overall_apr = (total_earnings / (total_signal * grt_price)) * 100 if total_signal > 0 and grt_price > 0 else 0

        st.write(f"Total Signal: {total_signal:,.2f} GRT")
        st.write(f"Overall APR: {overall_apr:.2f}%")
        st.write(f"Estimated Earnings:")
        st.write(f"- Daily: ${(total_earnings / 365):,.2f}")
        st.write(f"- Weekly: ${(total_earnings / 52):,.2f}")
        st.write(f"- Monthly: ${(total_earnings / 12):,.2f}")
        st.write(f"- Yearly: ${total_earnings:,.2f}")

        st.subheader("Low Performing Signals (APR < 1%)")
        low_performing = [opp for opp in user_opportunities if opp['apr'] < 1]
        if low_performing:
            low_df = pd.DataFrame([{
                'Signal (GRT)': round(opp['user_signal'], 2),
                'APR (%)': round(opp['apr'], 2),
                'IPFS Hash': opp['ipfs_hash']
            } for opp in low_performing])
            st.table(low_df.style.map(color_apr, subset=['APR (%)']))
        else:
            st.write("No signals with APR below 1%")

    if wallet_address:
        with tabs[1]:  # Your Current Curation Signal tab
            st.subheader("Your Current Curation Signal")
            
            st.write(f"Total Curated Signal: {total_signal:,.2f} GRT")
            st.write(f"Total Value of Curated Signal: ${(total_signal * grt_price):,.2f}")
            st.write(f"Estimated Annual Earnings: ${total_earnings:,.2f}")
            overall_apr = (total_earnings / (total_signal * grt_price)) * 100 if total_signal > 0 and grt_price > 0 else 0
            st.write(f"Overall APR: {overall_apr:.2f}%")
            
            user_data = []
            for opp in user_opportunities:
                user_data.append({
                    'Your Signal (GRT)': round(opp['user_signal'], 2) if opp['user_signal'] is not None else '-',
                    'Total Signal (GRT)': round(opp['total_signal'], 2) if opp['total_signal'] is not None else '-',
                    'Portion Owned': f"{opp['portion_owned']:.2%}" if opp['portion_owned'] is not None else '-',
                    'Estimated Annual Earnings ($)': round(opp['estimated_earnings'], 2) if opp['estimated_earnings'] is not None else '-',
                    'APR (%)': round(opp['apr'], 2) if opp['apr'] is not None else '-',
                    'Weekly Queries': opp['weekly_queries'] if opp['weekly_queries'] is not None else '-',
                    'IPFS Hash': opp['ipfs_hash']
                })
            
            user_df = pd.DataFrame(user_data)
            styled_user_df = user_df.style.map(color_apr, subset=['APR (%)'])
            st.table(styled_user_df)
        
        with tabs[2]:  # Find Opportunities tab
            st.subheader("Find Opportunities")
            
            # User Inputs specific to this tab
            total_signal_to_add = st.number_input("Total signal amount to add (GRT)", value=10000, min_value=0)
            num_subgraphs = st.number_input("Number of subgraphs to allocate across", value=5, min_value=1)

            # Calculate signal distribution
            top_opportunities = opportunities[:num_subgraphs]
            allocations = calculate_signal_distribution(top_opportunities, total_signal_to_add, grt_price)

            # Prepare data for display
            data = []
            total_estimated_earnings_after = 0
            total_allocated_signal = 0

            for opp in top_opportunities:
                ipfs_hash = opp['ipfs_hash']
                signal_amount_before = opp['signal_amount']
                signalled_tokens_before = opp['signalled_tokens']
                curator_share = opp['curator_share']
                weekly_queries = opp['weekly_queries']

                apr_before = opp['apr']

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

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            st.write(f"Signaling {total_signal_to_add:,.2f} GRT across {num_subgraphs} subgraphs to maximize rewards.")

            # Display the table with styling
            styled_df = df.style.map(color_apr, subset=['APR Before (%)', 'APR After (%)'])
            st.table(styled_df)

            # Signal Results
            st.subheader("Signal Results")
            st.write(f"Total GRT Signaled: {total_allocated_signal:,.2f} GRT")
            st.write(f"Total Value of Signaled GRT: ${(total_allocated_signal * grt_price):,.2f}")
            
            st.write("Estimated Earnings:")
            st.write(f"- Per Day: ${(total_estimated_earnings_after / 365):,.2f}")
            st.write(f"- Per Week: ${(total_estimated_earnings_after / 52):,.2f}")
            st.write(f"- Per Month: ${(total_estimated_earnings_after / 12):,.2f}")
            st.write(f"- Per Year: ${total_estimated_earnings_after:,.2f}")
            
            weighted_apr = sum(row['APR After (%)'] * row['Allocated Signal (GRT)'] for row in data if row['APR After (%)'] != '-' and row['Allocated Signal (GRT)'] != '-') / total_allocated_signal if total_allocated_signal > 0 else 0
            st.write(f"Overall APR: {weighted_apr:.2f}%")

        with tabs[3]:  # Full Subgraph List tab
            display_full_subgraph_list(opportunities)

if __name__ == "__main__":
    main()
