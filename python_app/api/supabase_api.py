import requests
import base64
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, Tuple
from utils.config import (
    SUPABASE_USERNAME,
    SUPABASE_PASSWORD,
    SUPABASE_API_URL,
    CACHE_TTL_LONG
)

def get_auth_headers() -> Dict[str, str]:
    """Generate authentication headers for Supabase API."""
    credentials = f"{SUPABASE_USERNAME}:{SUPABASE_PASSWORD}"
    auth_bytes = credentials.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    return {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

@st.cache_data(ttl=CACHE_TTL_LONG)
def query_supabase() -> list:
    """Query Supabase for query volume data."""
    try:
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
            SUPABASE_API_URL,
            headers=get_auth_headers(),
            json={"query": sql_query}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error executing query: HTTP {response.status_code} - {response.text}")

    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def process_query_data() -> Tuple[Dict[str, float], Dict[str, int]]:
    """Process query data from Supabase into fees and counts dictionaries."""
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
