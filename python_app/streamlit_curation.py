import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
from scipy.optimize import minimize
import statistics

# GraphQL query to get subgraph deployment data
@st.cache_data
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
@st.cache_data
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

@st.cache_data
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

@st.cache_data
def get_user_curation_signal(wallet_address):
    url = "https://gateway.thegraph.com/api/040d2183b97fb279ac2cb8fb2c78beae/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp"
    query = """
    {
      nameSignals(where: {curator: "%s", signal_gt: 10000}, first: 1000, orderBy: signal, orderDirection: desc) {
        subgraph {
          currentVersion {
            subgraphDeployment {
              ipfsHash
            }
          }
        }
        signal
      }
    }
    """ % wallet_address
    response = requests.post(url, json={'query': query})
    data = response.json()['data']['nameSignals']
    return {item['subgraph']['currentVersion']['subgraphDeployment']['ipfsHash']: float(item['signal']) / 1e18 for item in data}

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

    # Prepare data for display
    optimal_allocations = []
    total_estimated_earnings_after = 0
    total_allocated_signal = 0

    for opp in top_opportunities:
        ipfs_hash = opp['ipfs_hash']
        signal_amount_before = opp['signal_amount']
        signalled_tokens_before = opp['signalled_tokens']
        annual_fees = opp['total_earnings']
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

        optimal_allocations.append({
            'ipfs_hash': ipfs_hash,
            'allocated_signal': allocated_amount,
            'new_total_signal': signalled_tokens_after,
            'portion_owned': portion_owned_after,
            'estimated_earnings': estimated_earnings_after,
            'apr': apr_after,
            'weekly_queries': weekly_queries
        })

    return optimal_allocations

def calculate_signal_distribution(opportunities, total_signal, grt_price):
    # Sort opportunities by APR in descending order
    opportunities = sorted(opportunities, key=lambda x: x['apr'], reverse=True)

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

def display_full_subgraph_list(opportunities):
    st.subheader("Full Subgraph List")
    data = []
    for opp in opportunities:
        data.append({
            'IPFS Hash': opp['ipfs_hash'],
            'Signal (GRT)': round(opp['signal_amount'], 2),
            'Total Signal (GRT)': round(opp['signalled_tokens'], 2),
            'APR (%)': round(opp['apr'], 2),
            'Weekly Queries': opp['weekly_queries']
        })
    df = pd.DataFrame(data)
    styled_df = df.style.applymap(color_apr, subset=['APR (%)'])
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
    tab_labels = ["Summary", "Your Current Curation Signal", "Optimal Allocations", "Find Opportunities", "Full Subgraph List"]
    tabs = st.tabs(tab_labels)

    # Data Retrieval and Processing
    deployments = get_subgraph_deployments()
    query_fees, query_counts = process_csv_files('python_data/hourly_query_volume')
    grt_price = get_grt_price()
    opportunities = calculate_opportunities(deployments, query_fees, query_counts, grt_price)

    # Default wallet address
    default_wallet = "0x74dbb201ecc0b16934e68377bc13013883d9417b"

    with tabs[0]:  # Summary tab
        st.subheader("Summary")
        wallet_address = st.text_input("Enter your wallet address", value=default_wallet).lower()
        st.write(f"Current GRT Price: ${grt_price:.4f}")

        user_signals = get_user_curation_signal(wallet_address)
        user_opportunities = calculate_user_opportunities(user_signals, opportunities, grt_price)

        total_signal = sum(opp['user_signal'] for opp in user_opportunities)
        total_earnings = sum(opp['estimated_earnings'] for opp in user_opportunities)
        aprs = [opp['apr'] for opp in user_opportunities if opp['apr'] > 0]
        median_apr = statistics.median(aprs) if aprs else 0
        average_apr = statistics.mean(aprs) if aprs else 0

        st.write(f"Total Signal: {total_signal:,.2f} GRT")
        st.write(f"Median APR: {median_apr:.2f}%")
        st.write(f"Average APR: {average_apr:.2f}%")
        st.write(f"Estimated Earnings:")
        st.write(f"- Daily: ${total_earnings / 365:,.2f}")
        st.write(f"- Weekly: ${total_earnings / 52:,.2f}")
        st.write(f"- Monthly: ${total_earnings / 12:,.2f}")
        st.write(f"- Yearly: ${total_earnings:,.2f}")

        st.subheader("Low Performing Allocations (APR < 1%)")
        low_performing = [opp for opp in user_opportunities if opp['apr'] < 1]
        if low_performing:
            low_df = pd.DataFrame([{
                'IPFS Hash': opp['ipfs_hash'],
                'Signal (GRT)': round(opp['user_signal'], 2),
                'APR (%)': round(opp['apr'], 2)
            } for opp in low_performing])
            st.table(low_df.style.applymap(color_apr, subset=['APR (%)']))
        else:
            st.write("No allocations with APR below 1%")

    if wallet_address:
        with tabs[1]:  # Your Current Curation Signal tab
            st.subheader("Your Current Curation Signal")
            
            st.write(f"Total Curated Signal: {total_signal:,.2f} GRT")
            st.write(f"Total Value of Curated Signal: ${total_signal * grt_price:,.2f}")
            st.write(f"Estimated Annual Earnings: ${total_earnings:,.2f}")
            overall_apr = (total_earnings / (total_signal * grt_price)) * 100 if total_signal > 0 and grt_price > 0 else 0
            st.write(f"Overall APR: {overall_apr:.2f}%")
            
            user_data = []
            for opp in user_opportunities:
                user_data.append({
                    'IPFS Hash': opp['ipfs_hash'],
                    'Your Signal (GRT)': round(opp['user_signal'], 2) if opp['user_signal'] is not None else '-',
                    'Total Signal (GRT)': round(opp['total_signal'], 2) if opp['total_signal'] is not None else '-',
                    'Portion Owned': f"{opp['portion_owned']:.2%}" if opp['portion_owned'] is not None else '-',
                    'Estimated Annual Earnings ($)': round(opp['estimated_earnings'], 2) if opp['estimated_earnings'] is not None else '-',
                    'Current APR (%)': round(opp['apr'], 2) if opp['apr'] is not None else '-',
                    'Weekly Queries': opp['weekly_queries'] if opp['weekly_queries'] is not None else '-'
                })
            
            user_df = pd.DataFrame(user_data)
            styled_user_df = user_df.style.applymap(color_apr, subset=['Current APR (%)'])
            st.table(styled_user_df)
        
        with tabs[2]:  # Optimal Allocations tab
            st.subheader("Optimal Allocations")
            
            # Calculate optimal allocations
            optimal_allocations = calculate_optimal_allocations(opportunities, user_signals, total_signal, grt_price, num_subgraphs=20)
            
            total_optimal_earnings = sum(alloc['estimated_earnings'] for alloc in optimal_allocations)
            optimal_apr = (total_optimal_earnings / (total_signal * grt_price)) * 100 if total_signal > 0 and grt_price > 0 else 0
            
            st.write(f"Optimal Total Annual Earnings: ${total_optimal_earnings:,.2f}")
            st.write(f"Optimal Overall APR: {optimal_apr:.2f}%")
            
            apr_improvement = optimal_apr - overall_apr
            st.write(f"APR Improvement: {apr_improvement:.2f}%")
            st.write(f"Relative APR Improvement: {(apr_improvement / overall_apr) * 100:.2f}%")
            
            # Display optimal allocations
            optimal_data = []
            for alloc in optimal_allocations:
                optimal_data.append({
                    'IPFS Hash': alloc['ipfs_hash'],
                    'Optimal Signal (GRT)': round(alloc['allocated_signal'], 2) if alloc['allocated_signal'] is not None else '-',
                    'New Total Signal (GRT)': round(alloc['new_total_signal'], 2) if alloc['new_total_signal'] is not None else '-',
                    'Portion Owned': f"{alloc['portion_owned']:.2%}" if alloc['portion_owned'] is not None else '-',
                    'Estimated Annual Earnings ($)': round(alloc['estimated_earnings'], 2) if alloc['estimated_earnings'] is not None else '-',
                    'Optimal APR (%)': round(alloc['apr'], 2) if alloc['apr'] is not None else '-',
                    'Weekly Queries': alloc['weekly_queries'] if alloc['weekly_queries'] is not None else '-'
                })
            
            optimal_df = pd.DataFrame(optimal_data)
            styled_optimal_df = optimal_df.style.applymap(color_apr, subset=['Optimal APR (%)'])
            st.table(styled_optimal_df)

        with tabs[3]:  # Find Opportunities tab
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
                    'IPFS Hash': ipfs_hash,
                    'Signal Before (GRT)': round(signal_amount_before, 2) if signal_amount_before is not None else '-',
                    'Signal After (GRT)': round(signal_amount_after, 2) if signal_amount_after is not None else '-',
                    'APR Before (%)': round(apr_before, 2) if apr_before is not None else '-',
                    'APR After (%)': round(apr_after, 2) if apr_after is not None else '-',
                    'Earnings After ($)': round(estimated_earnings_after, 2) if estimated_earnings_after is not None else '-',
                    'Allocated Signal (GRT)': round(allocated_amount, 2) if allocated_amount is not None else '-',
                    'Weekly Queries': weekly_queries if weekly_queries is not None else '-'
                })

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            st.write(f"Signaling {total_signal_to_add} GRT across {num_subgraphs} subgraphs to maximize rewards.")

            # Display the table with styling
            styled_df = df.style.applymap(color_apr, subset=['APR Before (%)', 'APR After (%)'])
            st.table(styled_df)

            # Signal Results
            st.subheader("Signal Results")
            st.write(f"Total GRT Signaled: {total_allocated_signal:,.2f} GRT")
            st.write(f"Total Value of Signaled GRT: ${total_allocated_signal * grt_price:,.2f}")
            
            st.write("Estimated Earnings:")
            st.write(f"- Per Day: ${total_estimated_earnings_after / 365:,.2f}")
            st.write(f"- Per Week: ${total_estimated_earnings_after / 52:,.2f}")
            st.write(f"- Per Month: ${total_estimated_earnings_after / 12:,.2f}")
            st.write(f"- Per Year: ${total_estimated_earnings_after:,.2f}")
            
            weighted_apr = sum(row['APR After (%)'] * row['Allocated Signal (GRT)'] for row in data if row['APR After (%)'] != '-' and row['Allocated Signal (GRT)'] != '-') / total_allocated_signal if total_allocated_signal > 0 else 0
            st.write(f"Overall APR: {weighted_apr:.2f}%")

        with tabs[4]:  # Full Subgraph List tab
            display_full_subgraph_list(opportunities)

if __name__ == "__main__":
    main()
