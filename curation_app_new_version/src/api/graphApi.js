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

  // Query for BOTH nameSignals and deployment signals (older method)
  const query = `
    query GetUserCurationSignal($curator: String!) {
      curator(id: $curator) {
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
                id
                ipfsHash
                pricePerShare
                signalAmount
                signalledTokens
              }
            }
          }
        }
        signals(first: 1000) {
          id
          signalledTokens
          signal
          averageCostBasis
          realizedRewards
          subgraphDeployment {
            id
            ipfsHash
            signalAmount
            signalledTokens
          }
        }
      }
    }
  `;

  try {
    console.log('🔍 Fetching user signals (both types) for:', curator);
    const data = await graphClient.query(query, { curator });
    console.log('📊 Raw GraphQL response:', data);
    
    const curatorData = data?.curator;
    console.log('🎯 NameSignals found:', curatorData?.nameSignals?.length || 0);
    console.log('🎯 Deployment Signals found:', curatorData?.signals?.length || 0);
    
    const signals = [];
    const deploymentSignalMap = new Map(); // Track which deployments we've already processed
    
    // Process deployment signals first (older method)
    if (curatorData && curatorData.signals) {
      curatorData.signals.forEach((deploymentSignal, index) => {
        const deployment = deploymentSignal.subgraphDeployment;
        
        if (deployment && deployment.ipfsHash) {
          const signal = {
            id: deploymentSignal.id,
            signalledTokens: deploymentSignal.signalledTokens,
            signal: deploymentSignal.signal,
            averageCostBasis: deploymentSignal.averageCostBasis || '0',
            realizedRewards: deploymentSignal.realizedRewards || '0',
            subgraphDeployment: {
              id: deployment.id,
              ipfsHash: deployment.ipfsHash,
              signalledTokens: deployment.signalledTokens,
              signalAmount: deployment.signalAmount
            },
            curator: {
              id: curator
            },
            signalType: 'deployment' // Mark as deployment signal
          };
          
          signals.push(signal);
          deploymentSignalMap.set(deployment.ipfsHash, true);
          
          console.log(`🎯 Deployment Signal ${index + 1}:`, {
            signalledTokens: deploymentSignal.signalledTokens,
            signal: deploymentSignal.signal,
            ipfsHash: deployment.ipfsHash,
            type: 'deployment'
          });
        }
      });
    }
    
    // Process nameSignals (newer method) - only if not already covered by deployment signals
    if (curatorData && curatorData.nameSignals) {
      curatorData.nameSignals.forEach((nameSignal, index) => {
        const subgraph = nameSignal.subgraph;
        const deployment = subgraph?.currentVersion?.subgraphDeployment;
        
        if (deployment && deployment.ipfsHash) {
          // Skip if we already have a deployment signal for this IPFS hash
          if (!deploymentSignalMap.has(deployment.ipfsHash)) {
            const signal = {
              id: `${curator}-${deployment.ipfsHash}`,
              signalledTokens: nameSignal.signalledTokens,
              signal: nameSignal.signal,
              averageCostBasis: '0', // Not available in nameSignals
              realizedRewards: '0',  // Not available in nameSignals
              subgraphDeployment: {
                id: deployment.id,
                ipfsHash: deployment.ipfsHash,
                signalledTokens: deployment.signalledTokens,
                signalAmount: deployment.signalAmount
              },
              curator: {
                id: curator
              },
              signalType: 'name' // Mark as name signal
            };
            
            signals.push(signal);
            
            console.log(`🏷️ Name Signal ${index + 1}:`, {
              signalledTokens: nameSignal.signalledTokens,
              signal: nameSignal.signal,
              ipfsHash: deployment.ipfsHash,
              subgraphName: subgraph?.metadata?.displayName,
              type: 'name'
            });
          } else {
            console.log(`⚠️ Skipping nameSignal for ${deployment.ipfsHash} (already covered by deployment signal)`);
          }
        }
      });
    }
    
    console.log('✅ Total signals found (both types):', signals.length);
    console.log('📋 Signal breakdown:', {
      deploymentSignals: curatorData?.signals?.length || 0,
      nameSignals: curatorData?.nameSignals?.length || 0,
      totalUnique: signals.length
    });
    
    return signals;
  } catch (error) {
    console.error('❌ Error fetching user curation signals:', error);
    return [];
  }
}

export async function getGrtPrice() {
  try {
    // Use The Graph's OHLC price API
    const response = await fetch('https://token-api.thegraph.com/ohlc/prices/evm/0x9623063377ad1b27544c965ccd7342f7ea7e88c7?network_id=arbitrum-one&interval=1h&limit=1&page=1', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer eyJhbGciOiJLTVNFUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk4Nzc1NzYsImp0aSI6IjAxYzJkYjcxLWUxNTgtNDExYi04Njc2LWEyZDI0MWQ3ODVhYSIsImlhdCI6MTc0Mzg3NzU3NiwiaXNzIjoiZGZ1c2UuaW8iLCJzdWIiOiIweGFmaWM5YzczNWU3MDY2Y2RkODgiLCJ2IjoxLCJha2kiOiIwZDlmNmIxYjBhN2U3Y2M4NTg5NDExNzkyODIwNTU3MGI5ODQ3ZjMxNWQ3ZWM5YjI0Y2FkOTI0YmE2Y2FmOGZhIiwidWlkIjoiMHhhZmljOWM3MzVlNzA2NmNkZDg4In0.Q-7yDDxRGjmzkgkhKdIZovYOyRC5P5wjFm66JcmisFXj6cv9mtDV6oAtQdAn_p0a-1F9x_8KI8z3eBuJRqcW3w',
        'Accept': 'application/json'
      }
    });

    if (response.ok) {
      const priceData = await response.json();
      
      // Get the most recent close price from OHLC data
      if (priceData?.data && priceData.data.length > 0) {
        const latestPrice = priceData.data[0].close; // Most recent OHLC data
        console.log('💰 Fetched GRT price from The Graph API:', latestPrice);
        return latestPrice;
      }
    }
  } catch (error) {
    console.error('Error fetching GRT price from The Graph API:', error);
  }
  
  // Fallback to CoinGecko if The Graph API fails
  try {
    const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=the-graph&vs_currencies=usd');
    if (response.ok) {
      const priceData = await response.json();
      const price = priceData?.['the-graph']?.usd || 0.0892;
      console.log('💰 Fetched GRT price from CoinGecko (fallback):', price);
      return price;
    }
  } catch (error) {
    console.error('Error fetching GRT price from CoinGecko:', error);
  }
  
  return 0.0892; // Final fallback price
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