// The Graph API integration
const THEGRAPH_API_KEY = import.meta.env.VITE_THEGRAPH_API_KEY;
const GRAPH_API_URL = `https://gateway.thegraph.com/api/${THEGRAPH_API_KEY}/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp`;
const GRT_PRICE_API_URL = `https://gateway.thegraph.com/api/${THEGRAPH_API_KEY}/subgraphs/id/4RTrnxLZ4H8EBdpAQTcVc7LQY9kk85WNLyVzg5iXFQCH`;

class GraphQLClient {
  constructor(url) {
    this.url = url;
  }

  async query(query, variables = {}) {
    try {
      const response = await fetch(this.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          variables,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.errors) {
        console.error('GraphQL errors:', result.errors);
        throw new Error(`GraphQL errors: ${JSON.stringify(result.errors)}`);
      }

      return result.data;
    } catch (error) {
      console.error('GraphQL query error:', error);
      throw error;
    }
  }
}

const graphClient = new GraphQLClient(GRAPH_API_URL);
const grtPriceClient = new GraphQLClient(GRT_PRICE_API_URL);

export async function getSubgraphDeployments() {
  const query = `
    query GetSubgraphDeployments {
      subgraphDeployments(
        first: 1000,
        orderBy: signalledTokens,
        orderDirection: desc,
        where: { signalledTokens_gt: "1000000000000000000000" }
      ) {
        id
        ipfsHash
        signalledTokens
        signalAmount
        reserveRatio
        curatorSignals {
          id
          curator {
            id
          }
          signalledTokens
          signal
        }
      }
    }
  `;

  try {
    console.log('Fetching subgraph deployments...');
    const data = await graphClient.query(query);
    console.log('Fetched deployments:', data?.subgraphDeployments?.length || 0);
    return data.subgraphDeployments || [];
  } catch (error) {
    console.error('Error fetching subgraph deployments:', error);
    return [];
  }
}

export async function getUserCurationSignal(walletAddress) {
  if (!walletAddress) return [];

  // Ensure address is lowercase
  const curator = walletAddress.toLowerCase();

  const query = `
    query GetUserCurationSignal($curator: String!) {
      signals(
        where: { curator: $curator }
        orderBy: signalledTokens
        orderDirection: desc
      ) {
        id
        signalledTokens
        signal
        averageCostBasis
        realizedRewards
        subgraphDeployment {
          id
          ipfsHash
          signalledTokens
          signalAmount
        }
        curator {
          id
        }
      }
    }
  `;

  try {
    console.log('Fetching user signals for:', curator);
    const data = await graphClient.query(query, { curator });
    console.log('Fetched signals:', data?.signals?.length || 0);
    return data.signals || [];
  } catch (error) {
    console.error('Error fetching user curation signals:', error);
    return [];
  }
}

export async function getGrtPrice() {
  // For now, let's use a fixed price and enhance this later
  // You can integrate with price APIs like CoinGecko if needed
  try {
    // Simple price fetch from CoinGecko
    const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=the-graph&vs_currencies=usd');
    if (response.ok) {
      const priceData = await response.json();
      const price = priceData?.['the-graph']?.usd || 0.0892;
      console.log('Fetched GRT price:', price);
      return price;
    }
  } catch (error) {
    console.error('Error fetching GRT price:', error);
  }
  
  return 0.0892; // Fallback price
}

export async function getSubgraphMetrics(ipfsHash) {
  const query = `
    query GetSubgraphMetrics($ipfsHash: String!) {
      subgraphDeployment(id: $ipfsHash) {
        id
        ipfsHash
        signalledTokens
        signalAmount
        reserveRatio
        curatorSignals {
          id
          signalledTokens
          signal
          curator {
            id
          }
        }
      }
    }
  `;

  try {
    const data = await graphClient.query(query, { ipfsHash });
    return data.subgraphDeployment;
  } catch (error) {
    console.error('Error fetching subgraph metrics:', error);
    return null;
  }
} 