import requests
from typing import Dict, List, Optional
import streamlit as st
from utils.config import GRAPH_API_URL, GRT_PRICE_API_URL, CACHE_TTL_SHORT, CACHE_TTL_LONG

@st.cache_data(ttl=CACHE_TTL_LONG)
def get_subgraph_deployments() -> List[Dict]:
    """Fetch all subgraph deployments from The Graph API."""
    query_template = '''
    {
      subgraphDeployments(first: 1000, where: {id_gt: "%s", deniedAt: 0, signalledTokens_gt: "100000000000000000000"}, orderBy: id, orderDirection: asc) {
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
        response = requests.post(GRAPH_API_URL, json={'query': query})
        if response.status_code != 200:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")
        
        data = response.json()
        deployments = data['data']['subgraphDeployments']
        
        if not deployments:
            break
        
        all_deployments.extend(deployments)
        last_id = deployments[-1]['id']
    
    return all_deployments

@st.cache_data(ttl=CACHE_TTL_SHORT)
def get_grt_price() -> float:
    """Fetch current GRT price from The Graph API."""
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
    response = requests.post(GRT_PRICE_API_URL, json={'query': query})
    data = response.json()
    return float(data['data']['assetPairs'][0]['currentPrice'])

@st.cache_data(ttl=CACHE_TTL_LONG)
def get_user_curation_signal(wallet_address: str) -> Dict[str, float]:
    """Fetch user's curation signals from The Graph API."""
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
    
    response = requests.post(GRAPH_API_URL, json={'query': query, 'variables': variables})
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

@st.cache_data(ttl=CACHE_TTL_SHORT)
def get_account_balance(wallet_address: str) -> float:
    """Fetch account's GRT balance from The Graph API."""
    query = """
    query($wallet: String!) {
      graphAccounts(where: {id: $wallet}) {
        id
        balance
      }
    }
    """
    
    variables = {
        "wallet": wallet_address.lower()
    }
    
    response = requests.post(GRAPH_API_URL, json={'query': query, 'variables': variables})
    if response.status_code != 200:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")
    
    data = response.json()
    accounts = data.get('data', {}).get('graphAccounts', [])
    
    if accounts:
        # Convert balance from wei to GRT
        return float(accounts[0].get('balance', 0)) / 1e18
    return 0.0
