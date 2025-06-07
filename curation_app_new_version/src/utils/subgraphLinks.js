// Utility functions for generating subgraph links

// Generate The Graph Explorer URL for a subgraph deployment
export function getSubgraphExplorerUrl(deploymentId, ipfsHash) {
  // The Graph Explorer uses deployment IDs in the URL
  // Format: https://thegraph.com/explorer/subgraphs/{deploymentId}
  if (deploymentId) {
    return `https://thegraph.com/explorer/subgraphs/${deploymentId}`;
  }
  
  // Fallback: use IPFS hash if deployment ID is not available
  if (ipfsHash) {
    return `https://thegraph.com/explorer/subgraphs/${ipfsHash}`;
  }
  
  return null;
}

// Generate The Graph Studio URL (alternative)
export function getSubgraphStudioUrl(deploymentId) {
  if (deploymentId) {
    return `https://thegraph.com/studio/subgraph/${deploymentId}`;
  }
  return null;
}

// Generate IPFS gateway URL for subgraph metadata
export function getIpfsUrl(ipfsHash) {
  if (ipfsHash) {
    return `https://ipfs.io/ipfs/${ipfsHash}`;
  }
  return null;
}

// Open subgraph link in new tab
export function openSubgraphLink(deploymentId, ipfsHash) {
  const url = getSubgraphExplorerUrl(deploymentId, ipfsHash);
  if (url) {
    window.open(url, '_blank', 'noopener,noreferrer');
  } else {
    console.warn('No valid URL found for subgraph:', { deploymentId, ipfsHash });
  }
} 