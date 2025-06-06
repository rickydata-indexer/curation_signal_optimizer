// Curation opportunity calculation utilities
// Ported from python_app/models/opportunities.py and models/signals.py

const WEI_TO_GRT = 1e18;
const WEEKS_PER_YEAR = 52.1429;

// Helper function to convert Wei to GRT
function weiToGrt(weiValue) {
  return parseFloat(weiValue) / WEI_TO_GRT;
}

// Calculate curation opportunities from deployments and query data
export function calculateOpportunities(deployments, queryFees, queryCounts, grtPrice) {
  const opportunities = [];

  deployments.forEach(deployment => {
    const ipfsHash = deployment.ipfsHash;
    const signalledTokens = weiToGrt(deployment.signalledTokens);
    const weeklyQueryFees = queryFees[ipfsHash] || 0;
    const weeklyQueryCount = queryCounts[ipfsHash] || 0;

    // Calculate annual metrics
    const annualQueryFees = weeklyQueryFees * WEEKS_PER_YEAR;
    const annualQueryCount = weeklyQueryCount * WEEKS_PER_YEAR;

    // Calculate curator share (10% of query fees)
    const curatorShare = annualQueryFees * 0.10;

    // Calculate APR for this subgraph
    const totalSignalValue = signalledTokens * grtPrice;
    const apr = totalSignalValue > 0 ? (curatorShare / totalSignalValue) * 100 : 0;

    opportunities.push({
      id: ipfsHash,
      ipfs_hash: ipfsHash,
      subgraph_name: `Subgraph ${ipfsHash.slice(0, 8)}...`,
      signal_amount: signalledTokens,
      signalled_tokens: signalledTokens,
      annual_queries: annualQueryCount,
      total_earnings: annualQueryFees,
      curator_share: curatorShare,
      estimated_earnings: curatorShare,
      apr: apr,
      weekly_queries: weeklyQueryCount,
      weekly_query_fees: weeklyQueryFees,
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
    
    // Calculate user's estimated earnings based on their portion
    const estimatedEarnings = opportunity.curator_share * portionOwned;
    
    // Calculate APR for user's position
    const userSignalValue = signalAmount * grtPrice;
    const apr = userSignalValue > 0 ? (estimatedEarnings / userSignalValue) * 100 : 0;

    userOpportunities.push({
      id: `${signal.id}`,
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