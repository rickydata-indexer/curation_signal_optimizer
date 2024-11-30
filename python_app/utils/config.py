import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_USERNAME = os.getenv('SUPABASE_USERNAME')
SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD')
SUPABASE_BASE_URL = "http://supabasekong-so4w8gock004k8kw8ck84o80.94.130.17.180.sslip.io"
SUPABASE_API_URL = f"{SUPABASE_BASE_URL}/api/pg-meta/default/query"

# The Graph API configuration
THEGRAPH_API_KEY = os.getenv('THEGRAPH_API_KEY')
GRAPH_API_URL = f"https://gateway.thegraph.com/api/{THEGRAPH_API_KEY}/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp"
GRT_PRICE_API_URL = f"https://gateway.thegraph.com/api/{THEGRAPH_API_KEY}/subgraphs/id/4RTrnxLZ4H8EBdpAQTcVc7LQY9kk85WNLyVzg5iXFQCH"

# Default wallet for testing
DEFAULT_WALLET = "0x74dbb201ecc0b16934e68377bc13013883d9417b"

# Cache TTL settings (in seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_LONG = 1800  # 30 minutes
