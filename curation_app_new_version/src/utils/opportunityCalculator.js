// Curation opportunity calculation utilities
// Ported from python_app/models/opportunities.py and models/signals.py

const WEI_TO_GRT = 1e18;

// Helper function to convert Wei to GRT
function weiToGrt(weiValue) {
  return parseFloat(weiValue) / WEI_TO_GRT;
}

// Extract version ID from deployment versions array (remove part after the -)
function getVersionId(deployment) {
  if (deployment.versions && deployment.versions.length > 0) {
    const versionId = deployment.versions[0].id;
    // Remove the part after the dash (e.g., "9kVpuw3Cgf6NQckem8SXH7TQGXsJ8Hb8Zm6mQF7eaiyd-0" -> "9kVpuw3Cgf6NQckem8SXH7TQGXsJ8Hb8Zm6mQF7eaiyd")
    return versionId.split('-')[0];
  }
  return null;
}

// Extract version ID from user signal data (handles both deployment and name signals)
function getUserSignalVersionId(signal) {
  // For deployment signals, use the versions array
  if (signal.subgraphDeployment?.versions) {
    return getVersionId(signal.subgraphDeployment);
  }

  // For name signals, we might have the currentVersion.id directly
  // This would need to be added to the signal processing if available
  return null;
}

// Calculate curation opportunities from deployments and query data
export function calculateOpportunities(deployments, queryFees, queryCounts, grtPrice) {
  const opportunities = [];

  deployments.forEach(deployment => {
    const ipfsHash = deployment.ipfsHash;
    const signalledTokens = weiToGrt(deployment.signalledTokens);
    const annualQueryFees = queryFees[ipfsHash] || 0; // Already annual projections from API
    const annualQueryCount = queryCounts[ipfsHash] || 0; // Already annual projections from API

    // Calculate curator share (10% of query fees) - this is in GRT tokens
    const curatorShareGRT = annualQueryFees * 0.10;

    // Convert curator share from GRT to USD for APR calculation
    const curatorShareUSD = curatorShareGRT * grtPrice;

    // Calculate APR for this subgraph (both values now in USD)
    const totalSignalValue = signalledTokens * grtPrice;
    const apr = totalSignalValue > 0 ? (curatorShareUSD / totalSignalValue) * 100 : 0;

    // Convert annual back to daily for display purposes
    const dailyQueryFees = annualQueryFees / 365;
    const dailyQueryCount = annualQueryCount / 365;

    // Add detailed logging for high APR subgraphs or test subgraph
    if (apr > 100 || ipfsHash === 'QmdKXcBUHR3UyURqVRQHu1oV6VUkBrhi2vNvMx3bNDnUCc' || ipfsHash === 'QmRbn71wTNK3PmEb62wUK4G1XmKN14ZbHeTgi5JubL7evA') {
      console.log(`🔍 APR Calculation for ${ipfsHash}:`);
      console.log(`  📊 Signal: ${signalledTokens.toFixed(2)} GRT`);
      console.log(`  💰 GRT Price: $${grtPrice.toFixed(4)}`);
      console.log(`  💵 Signal Value: $${totalSignalValue.toFixed(2)}`);
      console.log(`  📈 Annual Query Fees: ${annualQueryFees.toFixed(2)} GRT (confirmed: GRT tokens)`);
      console.log(`  🎯 Curator Share: ${curatorShareGRT.toFixed(2)} GRT = $${curatorShareUSD.toFixed(2)} USD`);
      console.log(`  📋 APR: ${apr.toFixed(2)}% (FIXED: now using USD/USD)`);
      console.log(`  🔢 Weekly Queries: ${(dailyQueryCount * 7).toLocaleString()}`);
      console.log(`  ✅ Units: Query fees are GRT tokens, properly converted to USD`);
    }

    opportunities.push({
      id: ipfsHash,
      deployment_id: getVersionId(deployment), // Extract version ID for The Graph Explorer links
      ipfs_hash: ipfsHash,
      subgraph_name: `Subgraph ${ipfsHash.slice(0, 8)}...`,
      signal_amount: signalledTokens,
      signalled_tokens: signalledTokens,
      annual_queries: annualQueryCount,
      total_earnings: annualQueryFees,
      curator_share: curatorShareUSD,
      estimated_earnings: curatorShareUSD,
      apr: apr,
      daily_queries: dailyQueryCount,
      daily_query_fees: dailyQueryFees,
      weekly_queries: dailyQueryCount * 7, // Calculate weekly from daily for display
      weekly_query_fees: dailyQueryFees * 7, // Calculate weekly from daily for display
      reserve_ratio: deployment.reserveRatio || 0,
      curator_count: deployment.curatorSignals?.length || 0
    });
  });

  // Sort by APR descending
  return opportunities.sort((a, b) => b.apr - a.apr);
}

// Calculate user-specific opportunities from their current signals
export function calculateUserOpportunities(userSignals, allOpportunities, grtPrice) {
  const userOpportunities = [];

  userSignals.forEach(signal => {
    const ipfsHash = signal.subgraphDeployment?.ipfsHash;
    if (!ipfsHash) return;

    // Find the corresponding opportunity data
    const opportunity = allOpportunities.find(opp => opp.ipfs_hash === ipfsHash);
    if (!opportunity) return;

    const signalAmount = weiToGrt(signal.signalledTokens);
    const totalSignalAmount = weiToGrt(signal.subgraphDeployment.signalledTokens);
    
    // Calculate user's portion of the total signal
    const portionOwned = totalSignalAmount > 0 ? signalAmount / totalSignalAmount : 0;
    
    // Calculate user's estimated earnings based on their portion (curator_share is already in USD)
    const estimatedEarnings = opportunity.curator_share * portionOwned;
    
    // Calculate APR for user's position (both values in USD)
    const userSignalValue = signalAmount * grtPrice;
    const apr = userSignalValue > 0 ? (estimatedEarnings / userSignalValue) * 100 : 0;

    // Debug logging for the problematic subgraph
    if (ipfsHash === 'QmRbn71wTNK3PmEb62wUK4G1XmKN14ZbHeTgi5JubL7evA') {
      console.log(`🎯 User APR Calculation for ${ipfsHash}:`);
      console.log(`  👤 User Signal: ${signalAmount} GRT ($${userSignalValue.toFixed(2)})`);
      console.log(`  📊 Total Signal: ${totalSignalAmount} GRT`);
      console.log(`  🍰 Portion Owned: ${(portionOwned * 100).toFixed(2)}%`);
      console.log(`  💰 Total Curator Share: $${opportunity.curator_share.toFixed(2)}`);
      console.log(`  🎁 User Earnings: $${estimatedEarnings.toFixed(2)}`);
      console.log(`  📈 User APR: ${apr.toFixed(2)}%`);
    }

    userOpportunities.push({
      id: `${signal.id}`,
      deployment_id: getUserSignalVersionId(signal), // Extract version ID for The Graph Explorer links
      wallet_address: signal.curator?.id || '',
      ipfs_hash: ipfsHash,
      subgraph_name: `Subgraph ${ipfsHash.slice(0, 8)}...`,
      signal_amount: signalAmount,
      total_signal: totalSignalAmount,
      portion_owned: portionOwned,
      estimated_earnings: estimatedEarnings,
      apr: apr,
      weekly_queries: opportunity.weekly_queries,
      weekly_query_fees: opportunity.weekly_query_fees,
      average_cost_basis: weiToGrt(signal.averageCostBasis || 0),
      realized_rewards: weiToGrt(signal.realizedRewards || 0)
    });
  });

  // Sort by APR descending
  return userOpportunities.sort((a, b) => b.apr - a.apr);
}

// Calculate portfolio metrics
export function calculatePortfolioMetrics(userOpportunities, grtPrice) {
  if (!userOpportunities || userOpportunities.length === 0) {
    return {
      totalValue: 0,
      totalEarnings: 0,
      averageAPR: 0,
      totalSignalAmount: 0,
      positionCount: 0
    };
  }

  const totalSignalAmount = userOpportunities.reduce((sum, signal) => sum + signal.signal_amount, 0);
  const totalValue = totalSignalAmount * grtPrice;
  const totalEarnings = userOpportunities.reduce((sum, signal) => sum + signal.estimated_earnings, 0);
  
  // Calculate weighted average APR
  const weightedAPR = userOpportunities.reduce((sum, signal) => {
    const weight = totalValue > 0 ? (signal.signal_amount * grtPrice) / totalValue : 0;
    return sum + (signal.apr * weight);
  }, 0);

  return {
    totalValue,
    totalEarnings,
    averageAPR: weightedAPR,
    totalSignalAmount,
    positionCount: userOpportunities.length
  };
}

// Calculate diversification metrics
export function calculateDiversificationMetrics(userOpportunities) {
  if (!userOpportunities || userOpportunities.length === 0) {
    return {
      riskLevel: 'Unknown',
      diversificationScore: 0,
      optimizationScore: 0,
      concentration: 1.0
    };
  }

  const totalValue = userOpportunities.reduce((sum, signal) => sum + signal.signal_amount, 0);
  
  // Calculate Herfindahl-Hirschman Index for concentration
  const concentration = userOpportunities.reduce((sum, signal) => {
    const weight = totalValue > 0 ? signal.signal_amount / totalValue : 0;
    return sum + (weight * weight);
  }, 0);

  // Calculate risk level based on APR variance
  const averageAPR = userOpportunities.reduce((sum, signal) => sum + signal.apr, 0) / userOpportunities.length;
  const aprVariance = userOpportunities.reduce((sum, signal) => {
    return sum + Math.pow(signal.apr - averageAPR, 2);
  }, 0) / userOpportunities.length;
  
  const aprStdDev = Math.sqrt(aprVariance);
  
  let riskLevel = 'Low';
  if (aprStdDev > 10) riskLevel = 'High';
  else if (aprStdDev > 5) riskLevel = 'Medium';

  // Diversification score (inverse of concentration)
  const diversificationScore = Math.max(0, (1 - concentration) * 100);
  
  // Optimization score based on multiple factors
  const positionCount = userOpportunities.length;
  const positionScore = Math.min(100, positionCount * 20); // Better with more positions
  const aprScore = Math.min(100, averageAPR * 5); // Better with higher APR
  const optimizationScore = (diversificationScore + positionScore + aprScore) / 3;

  return {
    riskLevel,
    diversificationScore,
    optimizationScore,
    concentration
  };
}

// Find similar opportunities for recommendations
export function findSimilarOpportunities(userOpportunities, allOpportunities, limit = 5) {
  if (!userOpportunities || userOpportunities.length === 0) {
    return allOpportunities.slice(0, limit);
  }

  const userHashes = new Set(userOpportunities.map(signal => signal.ipfs_hash));
  const availableOpportunities = allOpportunities.filter(opp => !userHashes.has(opp.ipfs_hash));

  // Score opportunities based on similarity to user's current portfolio
  const userAverageAPR = userOpportunities.reduce((sum, signal) => sum + signal.apr, 0) / userOpportunities.length;
  
  const scoredOpportunities = availableOpportunities.map(opp => ({
    ...opp,
    similarityScore: 100 - Math.abs(opp.apr - userAverageAPR) // Higher score for similar APR
  }));

  return scoredOpportunities
    .sort((a, b) => b.similarityScore - a.similarityScore)
    .slice(0, limit);
} 